from django.conf import settings
from hashlib import md5
import os
import pickle
from ..exceptions import UnknownExtensionError
from ..files import GeneratedImageCacheFile, IKContentFile
from ..imagecache.backends import get_default_image_cache_backend
from ..imagecache.strategies import StrategyWrapper
from ..processors import ProcessorPipeline
from ..utils import (open_image, extension_to_format, img_to_fobj,
    suggest_extension)
from ..registry import generator_registry, register


class BaseImageSpec(object):
    """
    An object that defines how an new image should be generated from a source
    image.

    """

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
        self.image_cache_backend = self.image_cache_backend or get_default_image_cache_backend()
        self.image_cache_strategy = StrategyWrapper(self.image_cache_strategy)

    def generate(self):
        raise NotImplementedError

    # TODO: I don't like this interface. Is there a standard Python one? pubsub?
    def _handle_source_event(self, event_name, source_file):
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

    def __init__(self, source_file, **kwargs):
        self.source_file = source_file
        self.processors = self.processors or []
        self.kwargs = kwargs
        super(ImageSpec, self).__init__()

    def get_filename(self):
        source_filename = self.source_file.name
        ext = suggest_extension(source_filename, self.format)
        return os.path.normpath(os.path.join(
                settings.IMAGEKIT_CACHE_DIR,
                os.path.splitext(source_filename)[0],
                '%s%s' % (self.get_hash(), ext)))

        return os.path.join(settings.IMAGEKIT_CACHE_DIR,
                            '%s%s' % (hash, ext))

    def get_hash(self):
        return md5(''.join([
            self.source_file.name,
            pickle.dumps(self.kwargs),
            pickle.dumps(self.processors),
            str(self.format),
            pickle.dumps(self.options),
            str(self.autoconvert),
        ]).encode('utf-8')).hexdigest()

    def generate(self):
        # TODO: Move into a generator base class
        # TODO: Factor out a generate_image function so you can create a generator and only override the PIL.Image creating part. (The tricky part is how to deal with original_format since generator base class won't have one.)
        source_file = self.source_file
        filename = self.kwargs.get('filename')
        img = open_image(source_file)
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
        # TODO: Is this the right place to wrap the file? Can we use a mixin instead? Is it even still having the desired effect? Re: #111
        content = IKContentFile(filename, imgfile.read(), format=format)
        return content


def create_spec_class(class_attrs):
    cls = type('Spec', (DynamicSpec,), class_attrs)
    cls._spec_attrs = class_attrs
    return cls


def create_spec(class_attrs, kwargs):
    cls = create_spec_class(class_attrs)
    return cls(**kwargs)


class DynamicSpec(ImageSpec):
    def __reduce__(self):
        kwargs = dict(self.kwargs)
        kwargs['source_file'] = self.source_file
        return (create_spec, (self._spec_attrs, kwargs))


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
        register.spec(id, self._original_spec)

    def get_spec(self, **kwargs):
        """
        Look up the spec by the spec id. We do this (instead of storing the
        spec as an attribute) so that users can override apps' specs--without
        having to edit model definitions--simply by registering another spec
        with the same id.

        """
        if not getattr(self, 'spec_id', None):
            raise Exception('Object %s has no spec id.' % self)
        return generator_registry.get(self.spec_id, **kwargs)
