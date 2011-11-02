import os
import datetime
from StringIO import StringIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.db.models.fields.files import ImageFieldFile
from django.db.models.signals import post_save, post_delete
from django.utils.encoding import force_unicode, smart_str

from imagekit.lib import Image, ImageFile
from imagekit.utils import img_to_fobj, get_spec_files, open_image
from imagekit.processors import ProcessorPipeline

# Modify image file buffer size.
ImageFile.MAXBLOCK = getattr(settings, 'PIL_IMAGEFILE_MAXBLOCK', 256 * 2 ** 10)


class _ImageSpecMixin(object):
    def __init__(self, processors=None, quality=70, format=None):
        self.processors = processors
        self.quality = quality
        self.format = format

    def process(self, image, file):
        processors = ProcessorPipeline(self.processors)
        return processors.process(image.copy())


class ImageSpec(_ImageSpecMixin):
    """
    The heart and soul of the ImageKit library, ImageSpec allows you to add
    variants of uploaded images to your models.

    """
    _upload_to_attr = 'cache_to'

    def __init__(self, processors=None, quality=70, format=None,
        image_field=None, pre_cache=False, storage=None, cache_to=None):
        """
        :param processors: A list of processors to run on the original image.
        :param quality: The quality of the output image. This option is only
            used for the JPEG format.
        :param format: The format of the output file. If not provided,
            ImageSpec will try to guess the appropriate format based on the
            extension of the filename and the format of the input image.
        :param image_field: The name of the model property that contains the
            original image.
        :param pre_cache: A boolean that specifies whether the image should
            be generated immediately (True) or on demand (False).
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

        """

        _ImageSpecMixin.__init__(self, processors, quality=quality,
                format=format)
        self.image_field = image_field
        self.pre_cache = pre_cache
        self.storage = storage
        self.cache_to = cache_to

    def contribute_to_class(self, cls, name):
        setattr(cls, name, _ImageSpecDescriptor(self, name))
        try:
            ik = getattr(cls, '_ik')
        except AttributeError:
            ik = type('ImageKitMeta', (object,), {'spec_file_names': []})
            setattr(cls, '_ik', ik)
        ik.spec_file_names.append(name)

        # Connect to the signals only once for this class.
        uid = '%s.%s' % (cls.__module__, cls.__name__)
        post_save.connect(_post_save_handler,
            sender=cls,
            dispatch_uid='%s_save' % uid)
        post_delete.connect(_post_delete_handler,
            sender=cls,
            dispatch_uid='%s.delete' % uid)


def get_registered_extensions():
    Image.preinit()
    return Image.EXTENSION


def _get_suggested_extension(name, format):
    if format:
        # Try to look up an extension by the format.
        extensions = [k for k, v in get_registered_extensions().iteritems() \
                if v == format.upper()]
    else:
        extensions = []
    original_extension = os.path.splitext(name)[1]
    if not extensions or original_extension.lower() in extensions:
        # If the original extension matches the format, use it.
        extension = original_extension
    else:
        extension = extensions[0]
    return extension


class _ImageSpecFileMixin(object):
    def _process_content(self, filename, content):
        img = open_image(content)
        original_format = img.format
        img = self.field.process(img, self)

        # Determine the format.
        format = self.field.format
        if not format:
            if callable(getattr(self.field, self.field._upload_to_attr)):
                # The extension is explicit, so assume they want the matching format.
                extension = os.path.splitext(filename)[1].lower()
                # Try to guess the format from the extension.
                format = get_registered_extensions().get(extension)
        format = format or img.format or original_format or 'JPEG'

        if format != 'JPEG':
            imgfile = img_to_fobj(img, format)
        else:
            imgfile = img_to_fobj(img, format,
                                  quality=int(self.field.quality),
                                  optimize=True)
        content = ContentFile(imgfile.read())
        return img, content


class ImageSpecFile(_ImageSpecFileMixin, ImageFieldFile):
    def __init__(self, instance, field, attname, source_file):
        ImageFieldFile.__init__(self, instance, field, None)
        self.storage = field.storage or source_file.storage
        self.attname = attname
        self.source_file = source_file

    def _require_file(self):
        if not self.source_file:
            raise ValueError("The '%s' attribute's image_field has no file associated with it." % self.attname)

    def _get_file(self):
        self._create(True)
        return super(ImageFieldFile, self).file

    file = property(_get_file, ImageFieldFile._set_file, ImageFieldFile._del_file)

    @property
    def url(self):
        self._create(True)
        return super(ImageFieldFile, self).url

    def _create(self, lazy=False):
        """
        Creates a new image by running the processors on the source file.

        Keyword Arguments:
            lazy -- True if an already-existing image should be returned;
                False if a new image should be created and the existing
                one overwritten.

        """
        if lazy and (getattr(self, '_file', None) or self.storage.exists(self.name)):
            return

        if self.source_file:  # TODO: Should we error here or something if the source_file doesn't exist?
            # Process the original image file.
            try:
                fp = self.source_file.storage.open(self.source_file.name)
            except IOError:
                return
            fp.seek(0)
            fp = StringIO(fp.read())

            img, content = self._process_content(self.name, fp)
            self.storage.save(self.name, content)

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

        try:
            self.storage.delete(self.name)
        except (NotImplementedError, IOError):
            pass

        # Delete the filesize cache.
        if hasattr(self, '_size'):
            del self._size
        self._committed = False

        if save:
            self.instance.save()

    @property
    def _suggested_extension(self):
        return _get_suggested_extension(self.source_file.name, self.field.format)

    def _default_cache_to(self, instance, path, specname, extension):
        """
        Determines the filename to use for the transformed image. Can be
        overridden on a per-spec basis by setting the cache_to property on
        the spec.

        """
        filepath, basename = os.path.split(path)
        filename = os.path.splitext(basename)[0]
        new_name = '{0}_{1}{2}'.format(filename, specname, extension)
        return os.path.join(os.path.join('cache', filepath), new_name)

    @property
    def name(self):
        """
        Specifies the filename that the cached image will use. The user can
        control this by providing a `cache_to` method to the ImageSpec.

        """
        name = getattr(self, '_name', None)
        if not name:
            filename = self.source_file.name
            new_filename = None
            if filename:
                cache_to = self.field.cache_to or self._default_cache_to

                if not cache_to:
                    raise Exception('No cache_to or default_cache_to value specified')
                if callable(cache_to):
                    new_filename = force_unicode(datetime.datetime.now().strftime( \
                            smart_str(cache_to(self.instance, self.source_file.name,
                                self.attname, self._suggested_extension))))
                else:
                    dir_name = os.path.normpath(force_unicode(datetime.datetime.now().strftime(smart_str(cache_to))))
                    filename = os.path.normpath(os.path.basename(filename))
                    new_filename = os.path.join(dir_name, filename)

            self._name = new_filename
        return self._name

    @name.setter
    def name(self, value):
        # TODO: Figure out a better way to handle this. We really don't want
        # to allow anybody to set the name, but ``File.__init__`` (which is
        # called by ``ImageSpecFile.__init__``) does, so we have to allow it
        # at least that one time.
        pass


class _ImageSpecDescriptor(object):
    def __init__(self, field, attname):
        self.attname = attname
        self.field = field

    def _get_image_field_file(self, instance):
        field_name = getattr(self.field, 'image_field', None)
        if field_name:
            field = getattr(instance, field_name)
        else:
            image_fields = [getattr(instance, f.attname) for f in \
                    instance.__class__._meta.fields if \
                    isinstance(f, models.ImageField)]
            if len(image_fields) == 0:
                raise Exception('{0} does not define any ImageFields, so your '
                        '{1} ImageSpec has no image to act on.'.format(
                        instance.__class__.__name__, self.attname))
            elif len(image_fields) > 1:
                raise Exception('{0} defines multiple ImageFields, but you have '
                        'not specified an image_field for your {1} '
                        'ImageSpec.'.format(instance.__class__.__name__,
                        self.attname))
            else:
                field = image_fields[0]
        return field

    def __get__(self, instance, owner):
        if instance is None:
            return self.field
        else:
            img_spec_file = ImageSpecFile(instance, self.field,
                self.attname, self._get_image_field_file(instance))
            setattr(instance, self.attname, img_spec_file)
            return img_spec_file


def _post_save_handler(sender, instance=None, created=False, raw=False, **kwargs):
    if raw:
        return
    spec_files = get_spec_files(instance)
    for spec_file in spec_files:
        if not created:
            spec_file.delete(save=False)
        if spec_file.field.pre_cache:
            spec_file._create()


def _post_delete_handler(sender, instance=None, **kwargs):
    assert instance._get_pk_val() is not None, "%s object can't be deleted because its %s attribute is set to None." % (instance._meta.object_name, instance._meta.pk.attname)
    spec_files = get_spec_files(instance)
    for spec_file in spec_files:
        spec_file.delete(save=False)


class ProcessedImageFieldFile(ImageFieldFile, _ImageSpecFileMixin):
    def save(self, name, content, save=True):
        new_filename = self.field.generate_filename(self.instance, name)
        img, content = self._process_content(new_filename, content)
        return super(ProcessedImageFieldFile, self).save(name, content, save)


class ProcessedImageField(models.ImageField, _ImageSpecMixin):
    """
    ProcessedImageField is an ImageField that runs processors on the uploaded
    image *before* saving it to storage. This is in contrast to specs, which
    maintain the original. Useful for coercing fileformats or keeping images
    within a reasonable size.

    """
    _upload_to_attr = 'upload_to'
    attr_class = ProcessedImageFieldFile

    def __init__(self, processors=None, quality=70, format=None,
        verbose_name=None, name=None, width_field=None, height_field=None,
        **kwargs):
        """
        The ProcessedImageField constructor accepts all of the arguments that
        the :class:`django.db.models.ImageField` constructor accepts, as well
        as the ``processors``, ``format``, and ``quality`` arguments of
        :class:`imagekit.models.ImageSpec`.

        """
        _ImageSpecMixin.__init__(self, processors, quality=quality,
                format=format)
        models.ImageField.__init__(self, verbose_name, name, width_field,
                height_field, **kwargs)

    def get_filename(self, filename):
        filename = os.path.normpath(self.storage.get_valid_name(os.path.basename(filename)))
        name, ext = os.path.splitext(filename)
        ext = _get_suggested_extension(filename, self.format)
        return '{0}{1}'.format(name, ext)


try:
    from south.modelsinspector import add_introspection_rules
except ImportError:
    pass
else:
    add_introspection_rules([], [r'^imagekit\.models\.ProcessedImageField$'])
