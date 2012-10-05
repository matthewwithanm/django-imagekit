import os

from django.db import models
from django.db.models.signals import post_init, post_save, post_delete

from .files import ProcessedImageFieldFile
from .utils import ImageSpecFileDescriptor, ImageKitMeta
from ...base import ImageSpec
from ...utils import suggest_extension


class ImageSpecField(object):
    """
    The heart and soul of the ImageKit library, ImageSpecField allows you to add
    variants of uploaded images to your models.

    """
    def __init__(self, processors=None, format=None, options=None,
        image_field=None, storage=None, autoconvert=True,
        image_cache_backend=None, image_cache_strategy=None):

        # The spec accepts a callable value for processors, but it
        # takes different arguments than the callable that ImageSpecField
        # expects, so we create a partial application and pass that instead.
        # TODO: Should we change the signatures to match? Even if `instance` is not part of the signature, it's accessible through the source file object's instance property.
        p = lambda file: processors(instance=file.instance, file=file) if \
                callable(processors) else processors

        self.spec = ImageSpec(
            processors=p,
            format=format,
            options=options,
            storage=storage,
            autoconvert=autoconvert,
            image_cache_backend=image_cache_backend,
            image_cache_strategy=image_cache_strategy,
        )

        self.image_field = image_field

    @property
    def storage(self):
        return self.spec.storage

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
            self.spec.image_cache_backend.register_field(cls, self, name)
        except AttributeError:
            pass

    @staticmethod
    def _post_save_receiver(sender, instance=None, created=False, raw=False, **kwargs):
        if not raw:
            old_hashes = instance._ik._source_hashes.copy()
            new_hashes = ImageSpecField._update_source_hashes(instance)
            for attname in instance._ik.spec_fields:
                file = getattr(instance, attname)
                if created:
                    file.field.spec.image_cache_strategy.invoke_callback('source_create', file)
                elif old_hashes[attname] != new_hashes[attname]:
                    file.field.spec.image_cache_strategy.invoke_callback('source_change', file)

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
            spec_file.field.spec.image_cache_strategy.invoke_callback('source_delete', spec_file)

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

    def __init__(self, processors=None, format=None, options=None,
        verbose_name=None, name=None, width_field=None, height_field=None,
        autoconvert=True, **kwargs):
        """
        The ProcessedImageField constructor accepts all of the arguments that
        the :class:`django.db.models.ImageField` constructor accepts, as well
        as the ``processors``, ``format``, and ``options`` arguments of
        :class:`imagekit.models.ImageSpecField`.

        """
        models.ImageField.__init__(self, verbose_name, name, width_field,
                height_field, **kwargs)
        self.spec = ImageSpec(processors, format=format, options=options,
                autoconvert=autoconvert)

    def get_filename(self, filename):
        filename = os.path.normpath(self.storage.get_valid_name(
                os.path.basename(filename)))
        name, ext = os.path.splitext(filename)
        ext = suggest_extension(filename, self.spec.format)
        return u'%s%s' % (name, ext)


try:
    from south.modelsinspector import add_introspection_rules
except ImportError:
    pass
else:
    add_introspection_rules([], [r'^imagekit\.models\.fields\.ProcessedImageField$'])
