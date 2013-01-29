from django.conf import settings
from django.db.models.fields.files import ImageFieldFile
from hashlib import md5
import os
import pickle
from ..files import GeneratedImageCacheFile
from ..imagecache.backends import get_default_image_cache_backend
from ..imagecache.strategies import StrategyWrapper
from ..processors import ProcessorPipeline
from ..utils import open_image, img_to_fobj, suggest_extension
from ..registry import generator_registry, register


class BaseImageSpec(object):
    """
    An object that defines how an new image should be generated from a source
    image.

    """

    cache_file_storage = None
    """A Django storage system to use to save a generated cache file."""

    image_cache_backend = None
    """
    An object responsible for managing the state of cached files. Defaults to an
    instance of ``IMAGEKIT_DEFAULT_IMAGE_CACHE_BACKEND``

    """

    image_cache_strategy = settings.IMAGEKIT_DEFAULT_IMAGE_CACHE_STRATEGY
    """
    A dictionary containing callbacks that allow you to customize how and when
    the image cache is validated. Defaults to
    ``IMAGEKIT_DEFAULT_SPEC_FIELD_IMAGE_CACHE_STRATEGY``.

    """

    def __init__(self):
        self.image_cache_backend = self.image_cache_backend or get_default_image_cache_backend()
        self.image_cache_strategy = StrategyWrapper(self.image_cache_strategy)

    def generate(self):
        raise NotImplementedError

    # TODO: I don't like this interface. Is there a standard Python one? pubsub?
    def _handle_source_event(self, event_name, source):
        file = GeneratedImageCacheFile(self)
        self.image_cache_strategy.invoke_callback('on_%s' % event_name, file)


class ImageSpec(BaseImageSpec):
    """
    An object that defines how to generate a new image from a source file using
    PIL-based processors. (See :mod:`imagekit.processors`)

    """

    processors = None
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
        self.processors = self.processors or []
        super(ImageSpec, self).__init__()

    @property
    def cache_file_name(self):
        source_filename = getattr(self.source, 'name', None)

        if source_filename is None or os.path.isabs(source_filename):
            # Generally, we put the file right in the cache directory.
            dir = settings.IMAGEKIT_CACHE_DIR
        else:
            # For source files with relative names (like Django media files),
            # use the source's name to create the new filename.
            dir = os.path.join(settings.IMAGEKIT_CACHE_DIR,
                               os.path.splitext(source_filename)[0])

        ext = suggest_extension(source_filename or '', self.format)
        return os.path.normpath(os.path.join(dir,
                                             '%s%s' % (self.get_hash(), ext)))

    def __getstate__(self):
        state = self.__dict__

        # Unpickled ImageFieldFiles won't work (they're missing a storage
        # object). Since they're such a common use case, we special case them.
        if isinstance(self.source, ImageFieldFile):
            field = getattr(self.source, 'field')
            state['_field_data'] = {
                'instance': getattr(self.source, 'instance', None),
                'attname': getattr(field, 'name', None),
            }
        return state

    def __setstate__(self, state):
        field_data = state.pop('_field_data', None)
        self.__dict__ = state
        if field_data:
            self.source = getattr(field_data['instance'], field_data['attname'])

    def get_hash(self):
        return md5(pickle.dumps([
            self.source.name,
            self.processors,
            self.format,
            self.options,
            self.autoconvert,
        ])).hexdigest()

    def generate(self):
        # TODO: Move into a generator base class
        # TODO: Factor out a generate_image function so you can create a generator and only override the PIL.Image creating part. (The tricky part is how to deal with original_format since generator base class won't have one.)
        img = open_image(self.source)
        original_format = img.format

        # Run the processors
        processors = self.processors
        img = ProcessorPipeline(processors or []).process(img)

        options = dict(self.options or {})
        format = self.format or img.format or original_format or 'JPEG'
        content = img_to_fobj(img, format, **options)
        return content


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
        register.generator(id, self._original_spec)

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
