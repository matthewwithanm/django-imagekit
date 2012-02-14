import os
import datetime

from django.db import models
from django.db.models.fields.files import ImageFieldFile
from django.db.models.signals import post_init, post_save, post_delete
from django.utils.encoding import force_unicode, smart_str

from ..imagecache import get_default_image_cache_backend
from ..generators import SpecFileGenerator


class BoundImageKitMeta(object):
    def __init__(self, instance, spec_fields):
        self.instance = instance
        self.spec_fields = spec_fields

    @property
    def spec_files(self):
        return [getattr(self.instance, n) for n in self.spec_fields]


class ImageKitMeta(object):
    def __init__(self, spec_fields=None):
        self.spec_fields = spec_fields or []

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            ik = BoundImageKitMeta(instance, self.spec_fields)
            setattr(instance, '_ik', ik)
            return ik


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
        setattr(cls, name, _ImageSpecFieldDescriptor(self, name))
        try:
            ik = getattr(cls, '_ik')
        except AttributeError:
            ik = ImageKitMeta()
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


class ImageSpecFieldFile(ImageFieldFile):
    def __init__(self, instance, field, attname):
        ImageFieldFile.__init__(self, instance, field, None)
        self.attname = attname
        self.storage = self.field.storage or self.source_file.storage

    @property
    def source_file(self):
        field_name = getattr(self.field, 'image_field', None)
        if field_name:
            field_file = getattr(self.instance, field_name)
        else:
            image_fields = [getattr(self.instance, f.attname) for f in \
                    self.instance.__class__._meta.fields if \
                    isinstance(f, models.ImageField)]
            if len(image_fields) == 0:
                raise Exception('%s does not define any ImageFields, so your' \
                        ' %s ImageSpecField has no image to act on.' % \
                        (self.instance.__class__.__name__, self.attname))
            elif len(image_fields) > 1:
                raise Exception('%s defines multiple ImageFields, but you' \
                        ' have not specified an image_field for your %s' \
                        ' ImageSpecField.' % (self.instance.__class__.__name__,
                        self.attname))
            else:
                field_file = image_fields[0]
        return field_file

    def _require_file(self):
        if not self.source_file:
            raise ValueError("The '%s' attribute's image_field has no file associated with it." % self.attname)

    def _get_file(self):
        self.validate()
        return super(ImageFieldFile, self).file

    file = property(_get_file, ImageFieldFile._set_file, ImageFieldFile._del_file)

    def clear(self):
        return self.field.image_cache_backend.clear(self)

    def invalidate(self):
        return self.field.image_cache_backend.invalidate(self)

    def validate(self):
        return self.field.image_cache_backend.validate(self)

    def generate(self, save=True):
        """
        Generates a new image file by processing the source file and returns
        the content of the result, ready for saving.

        """
        return self.field.generator.generate_file(self.name, self.source_file,
                save)

    @property
    def url(self):
        self.validate()
        return super(ImageFieldFile, self).url

    def delete(self, save=False):
        """
        Pulled almost verbatim from ``ImageFieldFile.delete()`` and
        ``FieldFile.delete()`` but with the attempts to reset the instance
        property removed.

        """
        # Clear the image dimensions cache
        if hasattr(self, '_dimensions_cache'):
            del self._dimensions_cache

        # Only close the file if it's already open, which we know by the
        # presence of self._file.
        if hasattr(self, '_file'):
            self.close()
            del self.file

        if self.name and self.storage.exists(self.name):
            try:
                self.storage.delete(self.name)
            except NotImplementedError:
                pass

        # Delete the filesize cache.
        if hasattr(self, '_size'):
            del self._size
        self._committed = False

        if save:
            self.instance.save()

    def _default_cache_to(self, instance, path, specname, extension):
        """
        Determines the filename to use for the transformed image. Can be
        overridden on a per-spec basis by setting the cache_to property on
        the spec.

        """
        filepath, basename = os.path.split(path)
        filename = os.path.splitext(basename)[0]
        new_name = '%s_%s%s' % (filename, specname, extension)
        return os.path.join(os.path.join('cache', filepath), new_name)

    @property
    def name(self):
        """
        Specifies the filename that the cached image will use. The user can
        control this by providing a `cache_to` method to the ImageSpecField.

        """
        name = getattr(self, '_name', None)
        if not name:
            filename = self.source_file.name
            new_filename = None
            if filename:
                cache_to = self.field.cache_to or self._default_cache_to

                if not cache_to:
                    raise Exception('No cache_to or default_cache_to value'
                            ' specified')
                if callable(cache_to):
                    suggested_extension = \
                            self.field.generator.suggest_extension(
                            self.source_file.name)
                    new_filename = force_unicode(
                            datetime.datetime.now().strftime(
                            smart_str(cache_to(self.instance,
                            self.source_file.name, self.attname,
                            suggested_extension))))
                else:
                    dir_name = os.path.normpath(
                            force_unicode(datetime.datetime.now().strftime(
                            smart_str(cache_to))))
                    filename = os.path.normpath(os.path.basename(filename))
                    new_filename = os.path.join(dir_name, filename)

            self._name = new_filename
        return self._name

    @name.setter
    def name(self, value):
        # TODO: Figure out a better way to handle this. We really don't want
        # to allow anybody to set the name, but ``File.__init__`` (which is
        # called by ``ImageSpecFieldFile.__init__``) does, so we have to allow
        # it at least that one time.
        pass


class _ImageSpecFieldDescriptor(object):
    def __init__(self, field, attname):
        self.attname = attname
        self.field = field

    def __get__(self, instance, owner):
        if instance is None:
            return self.field
        else:
            img_spec_file = ImageSpecFieldFile(instance, self.field,
                    self.attname)
            setattr(instance, self.attname, img_spec_file)
            return img_spec_file


class ProcessedImageFieldFile(ImageFieldFile):
    def save(self, name, content, save=True):
        new_filename = self.field.generate_filename(self.instance, name)
        img, content = self.field.generator.process_content(content,
                new_filename, self)
        return super(ProcessedImageFieldFile, self).save(name, content, save)


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
        return '%s%s' % (name, ext)


try:
    from south.modelsinspector import add_introspection_rules
except ImportError:
    pass
else:
    add_introspection_rules([], [r'^imagekit\.models\.fields\.ProcessedImageField$'])
