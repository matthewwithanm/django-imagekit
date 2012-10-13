from django.conf import settings
from hashlib import md5
import os
import pickle
from .signals import source_created, source_changed, source_deleted
from ..exceptions import UnknownExtensionError, AlreadyRegistered, NotRegistered
from ..files import ImageSpecFile
from ..imagecache.backends import get_default_image_cache_backend
from ..imagecache.strategies import StrategyWrapper
from ..lib import StringIO
from ..processors import ProcessorPipeline
from ..utils import (open_image, extension_to_format, IKContentFile,
    img_to_fobj, suggest_extension)


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

    def register(self, id, spec):
        if id in self._specs:
            raise AlreadyRegistered('The spec with id %s is already registered' % id)
        self._specs[id] = spec

    def unregister(self, id, spec):
        try:
            del self._specs[id]
        except KeyError:
            raise NotRegistered('The spec with id %s is not registered' % id)

    def get_spec(self, id):
        try:
            return self._specs[id]
        except KeyError:
            raise NotRegistered('The spec with id %s is not registered' % id)

    def add_source(self, source, spec_id):
        """
        Associates a source with a spec id

        """
        if source not in self._sources:
            self._sources[source] = set()
        self._sources[source].add(spec_id)

    def source_receiver(self, sender, source_file, signal, **kwargs):
        """
        Redirects signals dispatched on sources to the appropriate specs.

        """
        source = sender
        if source not in self._sources:
            return

        for spec in (self.get_spec(id) for id in self._sources[source]):
            event_name = {
                source_created: 'source_created',
                source_changed: 'source_changed',
                source_deleted: 'source_deleted',
            }
            spec._handle_source_event(event_name, source_file)


class BaseImageSpec(object):
    processors = None
    format = None
    options = None
    autoconvert = True

    def __init__(self, processors=None, format=None, options=None, autoconvert=None):
        self.processors = processors or self.processors or []
        self.format = format or self.format
        self.options = options or self.options
        self.autoconvert = self.autoconvert if autoconvert is None else autoconvert

    def get_processors(self, source_file):
        processors = self.processors
        if callable(processors):
            processors = processors(source_file)
        return processors

    def get_hash(self, source_file):
        return md5(''.join([
            source_file.name,
            pickle.dumps(self.get_processors(source_file)),
            self.format,
            pickle.dumps(self.options),
            str(self.autoconvert),
        ]).encode('utf-8')).hexdigest()

    def generate_filename(self, source_file):
        source_filename = source_file.name
        filename = None
        if source_filename:
            hash = self.get_hash(source_file)
            extension = suggest_extension(source_filename, self.format)
            filename = os.path.normpath(os.path.join(
                    settings.IMAGEKIT_CACHE_DIR,
                    os.path.splitext(source_filename)[0],
                    '%s%s' % (hash, extension)))

        return filename

    def process_content(self, content, filename=None, source_file=None):
        img = open_image(content)
        original_format = img.format

        # Run the processors
        processors = self.get_processors(source_file)
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
        return img, content


class ImageSpec(BaseImageSpec):
    storage = None
    image_cache_backend = None
    image_cache_strategy = settings.IMAGEKIT_DEFAULT_IMAGE_CACHE_STRATEGY

    def __init__(self, processors=None, format=None, options=None,
        storage=None, autoconvert=None, image_cache_backend=None,
        image_cache_strategy=None):
        """
        :param processors: A list of processors to run on the original image.
        :param format: The format of the output file. If not provided,
            ImageSpecField will try to guess the appropriate format based on the
            extension of the filename and the format of the input image.
        :param options: A dictionary that will be passed to PIL's
            ``Image.save()`` method as keyword arguments. Valid options vary
            between formats, but some examples include ``quality``,
            ``optimize``, and ``progressive`` for JPEGs. See the PIL
            documentation for others.
        :param autoconvert: Specifies whether automatic conversion using
            ``prepare_image()`` should be performed prior to saving.
        :param image_field: The name of the model property that contains the
            original image.
        :param storage: A Django storage system to use to save the generated
            image.
        :param image_cache_backend: An object responsible for managing the state
            of cached files. Defaults to an instance of
            ``IMAGEKIT_DEFAULT_IMAGE_CACHE_BACKEND``
        :param image_cache_strategy: A dictionary containing callbacks that
            allow you to customize how and when the image cache is validated.
            Defaults to ``IMAGEKIT_DEFAULT_SPEC_FIELD_IMAGE_CACHE_STRATEGY``

        """
        super(ImageSpec, self).__init__(processors=processors, format=format,
                options=options, autoconvert=autoconvert)
        self.storage = storage or self.storage
        self.image_cache_backend = image_cache_backend or self.image_cache_backend or get_default_image_cache_backend()
        self.image_cache_strategy = StrategyWrapper(image_cache_strategy or self.image_cache_strategy)

    # TODO: Can we come up with a better name for this? "process" may cause confusion with processors' process()
    def apply(self, source_file):
        """
        Creates a file object that represents the combination of a spec and
        source file.

        """
        return ImageSpecFile(self, source_file)

    # TODO: I don't like this interface. Is there a standard Python one? pubsub?
    def _handle_source_event(self, event_name, source_file):
        file = self.apply(source_file)
        self.image_cache_strategy.invoke_callback('on_%s' % event_name, file)

    def generate_file(self, filename, source_file, save=True):
        """
        Generates a new image file by processing the source file and returns
        the content of the result, ready for saving.

        """
        if source_file:  # TODO: Should we error here or something if the source_file doesn't exist?
            # Process the original image file.

            try:
                fp = source_file.storage.open(source_file.name)
            except IOError:
                return
            fp.seek(0)
            fp = StringIO(fp.read())

            img, content = self.process_content(fp, filename, source_file)

            if save:
                storage = self.storage or source_file.storage
                storage.save(filename, content)

            return content


class SpecHost(object):
    """
    An object that ostensibly has a spec attribute but really delegates to the
    spec registry.

    """
    def __init__(self, processors=None, format=None, options=None,
            storage=None, autoconvert=None, image_cache_backend=None,
            image_cache_strategy=None, spec=None, spec_id=None):

        spec_args = dict(
            processors=processors,
            format=format,
            options=options,
            storage=storage,
            autoconvert=autoconvert,
            image_cache_backend=image_cache_backend,
            image_cache_strategy=image_cache_strategy,
        )

        if any(v is not None for v in spec_args.values()):
            if spec:
                raise TypeError('You can provide either an image spec or'
                    ' arguments for the ImageSpec constructor, but not both.')
            else:
                spec = ImageSpec(**spec_args)

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
        registry.register(id, self._original_spec)

    @property
    def spec(self):
        """
        Look up the spec by the spec id. We do this (instead of storing the
        spec as an attribute) so that users can override apps' specs--without
        having to edit model definitions--simply by registering another spec
        with the same id.

        """
        if not getattr(self, 'spec_id', None):
            raise Exception('Object %s has no spec id.' % self)
        return registry.get_spec(self.spec_id)


registry = SpecRegistry()
