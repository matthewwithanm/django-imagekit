from copy import copy
from django.conf import settings
from django.db.models.fields.files import ImageFieldFile
from ..cachefiles.backends import get_default_cachefile_backend
from ..cachefiles.strategies import load_strategy
from .. import hashers
from ..exceptions import AlreadyRegistered, MissingSource
from ..utils import open_image, get_by_qname, process_image
from ..registry import generator_registry, register


class BaseImageSpec(object):
    """
    An object that defines how an new image should be generated from a source
    image.

    """

    cachefile_storage = None
    """A Django storage system to use to save a cache file."""

    cachefile_backend = None
    """
    An object responsible for managing the state of cache files. Defaults to
    an instance of ``IMAGEKIT_DEFAULT_CACHEFILE_BACKEND``

    """

    cachefile_strategy = settings.IMAGEKIT_DEFAULT_CACHEFILE_STRATEGY
    """
    A dictionary containing callbacks that allow you to customize how and when
    the image file is created. Defaults to
    ``IMAGEKIT_DEFAULT_CACHEFILE_STRATEGY``.

    """

    def __init__(self):
        self.cachefile_backend = self.cachefile_backend or get_default_cachefile_backend()
        self.cachefile_strategy = load_strategy(self.cachefile_strategy)

    def generate(self):
        raise NotImplementedError

    MissingSource = MissingSource
    """
    Raised when an operation requiring a source is attempted on a spec that has
    no source.

    """


class ImageSpec(BaseImageSpec):
    """
    An object that defines how to generate a new image from a source file using
    PIL-based processors. (See :mod:`imagekit.processors`)

    """

    processors = []
    """A list of processors to run on the original image."""

    format = None
    """
    The format of the output file. If not provided, ImageSpecField will try to
    guess the appropriate format based on the extension of the filename and the
    format of the input image.

    """

    options = None
    """
    A dictionary that will be passed to PIL's ``Image.save()`` method as keyword
    arguments. Valid options vary between formats, but some examples include
    ``quality``, ``optimize``, and ``progressive`` for JPEGs. See the PIL
    documentation for others.

    """

    autoconvert = True
    """
    Specifies whether automatic conversion using ``prepare_image()`` should be
    performed prior to saving.

    """

    def __init__(self, source):
        self.source = source
        super(ImageSpec, self).__init__()

    @property
    def cachefile_name(self):
        if not self.source:
            return None
        fn = get_by_qname(settings.IMAGEKIT_SPEC_CACHEFILE_NAMER, 'namer')
        return fn(self)

    @property
    def source(self):
        src = getattr(self, '_source', None)
        if not src:
            field_data = getattr(self, '_field_data', None)
            if field_data:
                src = self._source = getattr(field_data['instance'], field_data['attname'])
                del self._field_data
        return src

    @source.setter
    def source(self, value):
        self._source = value

    def __getstate__(self):
        state = copy(self.__dict__)

        # Unpickled ImageFieldFiles won't work (they're missing a storage
        # object). Since they're such a common use case, we special case them.
        # Unfortunately, this also requires us to add the source getter to
        # lazily retrieve the source on the reconstructed object; simply trying
        # to look up the source in ``__setstate__`` would require us to get the
        # model instance but, if ``__setstate__`` was called as part of
        # deserializing that model, the model wouldn't be fully reconstructed
        # yet, preventing us from accessing the source field.
        # (This is issue #234.)
        if isinstance(self.source, ImageFieldFile):
            field = getattr(self.source, 'field')
            state['_field_data'] = {
                'instance': getattr(self.source, 'instance', None),
                'attname': getattr(field, 'name', None),
            }
            state.pop('_source', None)
        return state

    def get_hash(self):
        return hashers.pickle([
            self.source.name,
            self.processors,
            self.format,
            self.options,
            self.autoconvert,
        ])

    def generate(self):
        if not self.source:
            raise MissingSource("The spec '%s' has no source file associated"
                                " with it." % self)

        # TODO: Move into a generator base class
        # TODO: Factor out a generate_image function so you can create a generator and only override the PIL.Image creating part. (The tricky part is how to deal with original_format since generator base class won't have one.)

        closed = self.source.closed
        if closed:
            # Django file object should know how to reopen itself if it was closed
            # https://code.djangoproject.com/ticket/13750
            self.source.open()

        try:
            img = open_image(self.source)
            new_image = process_image(img,
                                      processors=self.processors,
                                      format=self.format,
                                      autoconvert=self.autoconvert,
                                      options=self.options)
        finally:
            if closed:
                # We need to close the file if it was opened by us
                self.source.close()
        return new_image


def create_spec_class(class_attrs):

    class DynamicSpecBase(ImageSpec):
        def __reduce__(self):
            try:
                getstate = self.__getstate__
            except AttributeError:
                state = self.__dict__
            else:
                state = getstate()
            return (create_spec, (class_attrs, state))

    return type('DynamicSpec', (DynamicSpecBase,), class_attrs)


def create_spec(class_attrs, state):
    cls = create_spec_class(class_attrs)
    instance = cls.__new__(cls)  # Create an instance without calling the __init__ (which may have required args).
    try:
        setstate = instance.__setstate__
    except AttributeError:
        instance.__dict__ = state
    else:
        setstate(state)
    return instance


class SpecHost(object):
    """
    An object that ostensibly has a spec attribute but really delegates to the
    spec registry.

    """
    def __init__(self, spec=None, spec_id=None, **kwargs):

        spec_attrs = dict((k, v) for k, v in kwargs.items() if v is not None)

        if spec_attrs:
            if spec:
                raise TypeError('You can provide either an image spec or'
                    ' arguments for the ImageSpec constructor, but not both.')
            else:
                spec = create_spec_class(spec_attrs)

        self._original_spec = spec

        if spec_id:
            self.set_spec_id(spec_id)

    def set_spec_id(self, id):
        """
        Sets the spec id for this object. Useful for when the id isn't
        known when the instance is constructed (e.g. for ImageSpecFields whose
        generated `spec_id`s are only known when they are contributed to a
        class). If the object was initialized with a spec, it will be registered
        under the provided id.

        """
        self.spec_id = id

        if self._original_spec:
            try:
                register.generator(id, self._original_spec)
            except AlreadyRegistered:
                # Fields should not cause AlreadyRegistered exceptions. If a
                # spec is already registered, that should be used. It is
                # especially important that an error is not thrown here because
                # of South, which will create duplicate models as part of its
                # "fake orm," therefore re-registering specs.
                pass

    def get_spec(self, source):
        """
        Look up the spec by the spec id. We do this (instead of storing the
        spec as an attribute) so that users can override apps' specs--without
        having to edit model definitions--simply by registering another spec
        with the same id.

        """
        if not getattr(self, 'spec_id', None):
            raise Exception('Object %s has no spec id.' % self)
        return generator_registry.get(self.spec_id, source=source)
