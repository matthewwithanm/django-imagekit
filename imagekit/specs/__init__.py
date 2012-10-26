from django.conf import settings
from hashlib import md5
import os
import pickle
from ..exceptions import (UnknownExtensionError, AlreadyRegistered,
                          NotRegistered, MissingSpecId)
from ..files import ImageSpecCacheFile, IKContentFile
from ..imagecache.backends import get_default_image_cache_backend
from ..imagecache.strategies import StrategyWrapper
from ..processors import ProcessorPipeline
from ..signals import (before_access, source_created, source_changed,
                       source_deleted)
from ..utils import open_image, extension_to_format, img_to_fobj


class SpecRegistry(object):
    """
    An object for registering specs and sources. The two are associated with
    eachother via a string id. We do this (as opposed to associating them
    directly by, for example, putting a ``sources`` attribute on specs) so that
    specs can be overridden without losing the associated sources. That way,
    a distributable app can define its own specs without locking the users of
    the app into it.

    """

    _source_signals = [
        source_created,
        source_changed,
        source_deleted,
    ]

    def __init__(self):
        self._specs = {}
        self._sources = {}
        for signal in self._source_signals:
            signal.connect(self.source_receiver)
        before_access.connect(self.before_access_receiver)

    def register(self, spec, id=None):
        config = getattr(spec, 'Config', None)

        if id is None:
            id = getattr(config, 'id', None)

        if id is None:
            raise MissingSpecId('No id provided for %s. You must either pass an'
                                ' id to the register function, or add an id'
                                ' attribute to the inner Config class of your'
                                ' spec.' % spec)

        if id in self._specs:
            raise AlreadyRegistered('The spec with id %s is already registered' % id)
        self._specs[id] = spec

        sources = getattr(config, 'sources', None) or []
        self.add_sources(id, sources)

    def unregister(self, id, spec):
        try:
            del self._specs[id]
        except KeyError:
            raise NotRegistered('The spec with id %s is not registered' % id)

    def get_spec(self, id, **kwargs):
        try:
            spec = self._specs[id]
        except KeyError:
            raise NotRegistered('The spec with id %s is not registered' % id)
        if callable(spec):
            return spec(**kwargs)
        else:
            return spec

    def get_spec_ids(self):
        return self._specs.keys()

    def add_sources(self, spec_id, sources):
        """
        Associates sources with a spec id

        """
        for source in sources:
            if source not in self._sources:
                self._sources[source] = set()
            self._sources[source].add(spec_id)

    def get_sources(self, spec_id):
        return [source for source in self._sources if spec_id in self._sources[source]]

    def before_access_receiver(self, sender, spec, file, **kwargs):
        spec.image_cache_strategy.invoke_callback('before_access', file)

    def source_receiver(self, sender, source_file, signal, info, **kwargs):
        """
        Redirects signals dispatched on sources to the appropriate specs.

        """
        source = sender
        if source not in self._sources:
            return

        for spec in (self.get_spec(id, source_file=source_file, **info)
                     for id in self._sources[source]):
            event_name = {
                source_created: 'source_created',
                source_changed: 'source_changed',
                source_deleted: 'source_deleted',
            }
            spec._handle_source_event(event_name, source_file)


class BaseImageSpec(object):

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

    def __init__(self):
        self.processors = self.processors or []

    def get_hash(self):
        return md5(''.join([
            pickle.dumps(self.processors),
            str(self.format),
            pickle.dumps(self.options),
            str(self.autoconvert),
        ]).encode('utf-8')).hexdigest()

    def apply(self, content, filename=None):
        img = open_image(content)
        original_format = img.format

        # Run the processors
        processors = self.processors
        img = ProcessorPipeline(processors or []).process(img)

        options = dict(self.options or {})

        # Determine the format.
        format = self.format
        if filename and not format:
            # Try to guess the format from the extension.
            extension = os.path.splitext(filename)[1].lower()
            if extension:
                try:
                    format = extension_to_format(extension)
                except UnknownExtensionError:
                    pass
        format = format or img.format or original_format or 'JPEG'

        imgfile = img_to_fobj(img, format, **options)
        content = IKContentFile(filename, imgfile.read(), format=format)
        return content


class ImageSpec(BaseImageSpec):

    storage = None
    """A Django storage system to use to save the generated image."""

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

    def __init__(self, **kwargs):
        super(ImageSpec, self).__init__()
        self.image_cache_backend = self.image_cache_backend or get_default_image_cache_backend()
        self.image_cache_strategy = StrategyWrapper(self.image_cache_strategy)

    # TODO: I don't like this interface. Is there a standard Python one? pubsub?
    def _handle_source_event(self, event_name, source_file):
        file = ImageSpecCacheFile(self, source_file)
        self.image_cache_strategy.invoke_callback('on_%s' % event_name, file)


class SpecHost(object):
    """
    An object that ostensibly has a spec attribute but really delegates to the
    spec registry.

    """
    def __init__(self, spec=None, spec_id=None, **kwargs):

        spec_args = dict((k, v) for k, v in kwargs.items() if v is not None)

        if spec_args:
            if spec:
                raise TypeError('You can provide either an image spec or'
                    ' arguments for the ImageSpec constructor, but not both.')
            else:
                spec = type('Spec', (ImageSpec,), spec_args)  # TODO: Base class name on spec id?

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
        registry.register(self._original_spec, id)

    def get_spec(self, **kwargs):
        """
        Look up the spec by the spec id. We do this (instead of storing the
        spec as an attribute) so that users can override apps' specs--without
        having to edit model definitions--simply by registering another spec
        with the same id.

        """
        if not getattr(self, 'spec_id', None):
            raise Exception('Object %s has no spec id.' % self)
        return registry.get_spec(self.spec_id, **kwargs)


registry = SpecRegistry()
register = registry.register


def unregister(id, spec):
    registry.unregister(id, spec)
