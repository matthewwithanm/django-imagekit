from django.conf import settings
from hashlib import md5
import os
import pickle
from .exceptions import UnknownExtensionError, AlreadyRegistered, NotRegistered
from .imagecache.backends import get_default_image_cache_backend
from .imagecache.strategies import StrategyWrapper
from .lib import StringIO
from .processors import ProcessorPipeline
from .utils import (open_image, extension_to_format, IKContentFile, img_to_fobj,
    suggest_extension)


class SpecRegistry(object):
    def __init__(self):
        self._specs = {}

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


spec_registry = SpecRegistry()


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
