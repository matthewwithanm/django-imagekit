import os

from django.db import models
from django.db.models.signals import post_init, post_save, post_delete

from ...imagecache import get_default_image_cache_backend
from ...generators import SpecFileGenerator
from .files import ImageSpecFieldFile, ProcessedImageFieldFile
from .utils import ImageSpecFileDescriptor, ImageKitMeta, BoundImageKitMeta


class ImageSpecField(object):
    """
    The heart and soul of the ImageKit library, ImageSpecField allows you to add
    variants of uploaded images to your models.

    """
    def __init__(self, processors=None, format=None, options={},
        image_field=None, pre_cache=None, storage=None, cache_to=None,
        autoconvert=True, image_cache_backend=None):
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
        :param image_field: The name of the model property that contains the
            original image.
        :param storage: A Django storage system to use to save the generated
            image.
        :param cache_to: Specifies the filename to use when saving the image
            cache file. This is modeled after ImageField's ``upload_to`` and
            can be either a string (that specifies a directory) or a
            callable (that returns a filepath). Callable values should
            accept the following arguments:

                - instance -- The model instance this spec belongs to
                - path -- The path of the original image
                - specname -- the property name that the spec is bound to on
                    the model instance
                - extension -- A recommended extension. If the format of the
                    spec is set explicitly, this suggestion will be
                    based on that format. if not, the extension of the
                    original file will be passed. You do not have to use
                    this extension, it's only a recommendation.
        :param autoconvert: Specifies whether the AutoConvert processor
            should be run before saving.
        :param image_cache_backend: An object responsible for managing the state
            of cached files. Defaults to an instance of
            IMAGEKIT_DEFAULT_IMAGE_CACHE_BACKEND

        """

        if pre_cache is not None:
            raise Exception('The pre_cache argument has been removed in favor'
                    ' of cache state backends.')

        # The generator accepts a callable value for processors, but it
        # takes different arguments than the callable that ImageSpecField
        # expects, so we create a partial application and pass that instead.
        # TODO: Should we change the signatures to match? Even if `instance` is not part of the signature, it's accessible through the source file object's instance property.
        p = lambda file: processors(instance=file.instance, file=file) if \
                callable(processors) else processors

        self.generator = SpecFileGenerator(p, format=format, options=options,
                autoconvert=autoconvert, storage=storage)
        self.image_field = image_field
        self.storage = storage
        self.cache_to = cache_to
        self.image_cache_backend = image_cache_backend or \
                get_default_image_cache_backend()

    def contribute_to_class(self, cls, name):
        setattr(cls, name, ImageSpecFileDescriptor(self, name))
        try:
            # Make sure we don't modify an inherited ImageKitMeta instance
            ik = cls.__dict__['ik']
        except KeyError:
            try:
                base = getattr(cls, '_ik')
            except AttributeError:
                ik = ImageKitMeta()
            else:
                # Inherit all the spec fields.
                ik = ImageKitMeta(base.spec_fields)
            setattr(cls, '_ik', ik)
        ik.spec_fields.append(name)

        # Connect to the signals only once for this class.
        uid = '%s.%s' % (cls.__module__, cls.__name__)
        post_init.connect(ImageSpecField._post_init_receiver, sender=cls,
                dispatch_uid=uid)
        post_save.connect(ImageSpecField._post_save_receiver, sender=cls,
                dispatch_uid=uid)
        post_delete.connect(ImageSpecField._post_delete_receiver, sender=cls,
                dispatch_uid=uid)

        # Register the field with the image_cache_backend
        try:
            self.image_cache_backend.register_field(cls, self, name)
        except AttributeError:
            pass

    @staticmethod
    def _post_save_receiver(sender, instance=None, created=False, raw=False, **kwargs):
        if not raw:
            old_hashes = instance._ik._source_hashes.copy()
            new_hashes = ImageSpecField._update_source_hashes(instance)
            for attname in instance._ik.spec_fields:
                if old_hashes[attname] != new_hashes[attname]:
                    getattr(instance, attname).invalidate()

    @staticmethod
    def _update_source_hashes(instance):
        """
        Stores hashes of the source image files so that they can be compared
        later to see whether the source image has changed (and therefore whether
        the spec file needs to be regenerated).

        """
        instance._ik._source_hashes = dict((f.attname, hash(f.source_file)) \
                for f in instance._ik.spec_files)
        return instance._ik._source_hashes

    @staticmethod
    def _post_delete_receiver(sender, instance=None, **kwargs):
        for spec_file in instance._ik.spec_files:
            spec_file.clear()

    @staticmethod
    def _post_init_receiver(sender, instance, **kwargs):
        ImageSpecField._update_source_hashes(instance)


class ProcessedImageField(models.ImageField):
    """
    ProcessedImageField is an ImageField that runs processors on the uploaded
    image *before* saving it to storage. This is in contrast to specs, which
    maintain the original. Useful for coercing fileformats or keeping images
    within a reasonable size.

    """
    attr_class = ProcessedImageFieldFile

    def __init__(self, processors=None, format=None, options={},
        verbose_name=None, name=None, width_field=None, height_field=None,
        autoconvert=True, **kwargs):
        """
        The ProcessedImageField constructor accepts all of the arguments that
        the :class:`django.db.models.ImageField` constructor accepts, as well
        as the ``processors``, ``format``, and ``options`` arguments of
        :class:`imagekit.models.fields.ImageSpecField`.

        """
        if 'quality' in kwargs:
            raise Exception('The "quality" keyword argument has been'
                    """ deprecated. Use `options={'quality': %s}` instead.""" \
                    % kwargs['quality'])
        models.ImageField.__init__(self, verbose_name, name, width_field,
                height_field, **kwargs)
        self.generator = SpecFileGenerator(processors, format=format,
                options=options, autoconvert=autoconvert)

    def get_filename(self, filename):
        filename = os.path.normpath(self.storage.get_valid_name(
                os.path.basename(filename)))
        name, ext = os.path.splitext(filename)
        ext = self.generator.suggest_extension(filename)
        return u'%s%s' % (name, ext)


try:
    from south.modelsinspector import add_introspection_rules
except ImportError:
    pass
else:
    add_introspection_rules([], [r'^imagekit\.models\.fields\.ProcessedImageField$'])
