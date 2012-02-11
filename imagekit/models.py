import os
import datetime
from StringIO import StringIO

from django.core.files.base import ContentFile
from django.db import models
from django.db.models.fields.files import ImageFieldFile
from django.db.models.signals import post_init, post_save, post_delete
from django.utils.encoding import force_unicode, smart_str

from imagekit.utils import img_to_fobj, open_image, \
        format_to_extension, extension_to_format, UnknownFormatError, \
        UnknownExtensionError
from imagekit.processors import ProcessorPipeline, AutoConvert
from .cachestate import get_default_cache_state_backend


class _ImageSpecMixin(object):
    def __init__(self, processors=None, format=None, options={},
            autoconvert=True):
        self.processors = processors
        self.format = format
        self.options = options
        self.autoconvert = autoconvert

    def process(self, image, file, instance):
        processors = self.processors
        if callable(processors):
            processors = processors(instance=instance, file=file)
        processors = ProcessorPipeline(processors or [])
        return processors.process(image.copy())


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


class ImageSpec(_ImageSpecMixin):
    """
    The heart and soul of the ImageKit library, ImageSpec allows you to add
    variants of uploaded images to your models.

    """
    _upload_to_attr = 'cache_to'

    def __init__(self, processors=None, format=None, options={},
        image_field=None, pre_cache=None, storage=None, cache_to=None,
        autoconvert=True, cache_state_backend=None):
        """
        :param processors: A list of processors to run on the original image.
        :param format: The format of the output file. If not provided,
            ImageSpec will try to guess the appropriate format based on the
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
        :param cache_state_backend: An object responsible for managing the state
            of cached files. Defaults to an instance of
            IMAGEKIT_DEFAULT_CACHE_STATE_BACKEND

        """

        if pre_cache is not None:
            raise Exception('The pre_cache argument has been removed in favor'
                    ' of cache state backends.')

        _ImageSpecMixin.__init__(self, processors, format=format,
                options=options, autoconvert=autoconvert)
        self.image_field = image_field
        self.pre_cache = pre_cache
        self.storage = storage
        self.cache_to = cache_to
        self.cache_state_backend = cache_state_backend or \
                get_default_cache_state_backend()

    def contribute_to_class(self, cls, name):
        setattr(cls, name, _ImageSpecDescriptor(self, name))
        try:
            ik = getattr(cls, '_ik')
        except AttributeError:
            ik = ImageKitMeta()
            setattr(cls, '_ik', ik)
        ik.spec_fields.append(name)

        # Connect to the signals only once for this class.
        uid = '%s.%s' % (cls.__module__, cls.__name__)
        post_init.connect(ImageSpec._post_init_receiver, sender=cls,
                dispatch_uid=uid)
        post_save.connect(ImageSpec._post_save_receiver, sender=cls,
                dispatch_uid=uid)
        post_delete.connect(ImageSpec._post_delete_receiver, sender=cls,
                dispatch_uid=uid)

        # Register the field with the cache_state_backend
        try:
            self.cache_state_backend.register_field(cls, self, name)
        except AttributeError:
            pass

    @staticmethod
    def _post_save_receiver(sender, instance=None, created=False, raw=False, **kwargs):
        if not raw:
            old_hashes = instance._ik._source_hashes.copy()
            new_hashes = ImageSpec._update_source_hashes(instance)
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
        ImageSpec._update_source_hashes(instance)


def _get_suggested_extension(name, format):
    original_extension = os.path.splitext(name)[1]
    try:
        suggested_extension = format_to_extension(format)
    except UnknownFormatError:
        extension = original_extension
    else:
        if suggested_extension.lower() == original_extension.lower():
            extension = original_extension
        else:
            try:
                original_format = extension_to_format(original_extension)
            except UnknownExtensionError:
                extension = suggested_extension
            else:
                # If the formats match, give precedence to the original extension.
                if format.lower() == original_format.lower():
                    extension = original_extension
                else:
                    extension = suggested_extension
    return extension


class _ImageSpecFileMixin(object):
    def _process_content(self, filename, content):
        img = open_image(content)
        original_format = img.format
        img = self.field.process(img, self, self.instance)
        options = dict(self.field.options or {})

        # Determine the format.
        format = self.field.format
        if not format:
            if callable(getattr(self.field, self.field._upload_to_attr)):
                # The extension is explicit, so assume they want the matching format.
                extension = os.path.splitext(filename)[1].lower()
                # Try to guess the format from the extension.
                try:
                    format = extension_to_format(extension)
                except UnknownExtensionError:
                    pass
        format = format or img.format or original_format or 'JPEG'

        # Run the AutoConvert processor
        if getattr(self.field, 'autoconvert', True):
            autoconvert_processor = AutoConvert(format)
            img = autoconvert_processor.process(img)
            options = dict(autoconvert_processor.save_kwargs.items() + \
                    options.items())

        imgfile = img_to_fobj(img, format, **options)
        content = ContentFile(imgfile.read())
        return img, content


class ImageSpecFile(_ImageSpecFileMixin, ImageFieldFile):
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
                        ' %s ImageSpec has no image to act on.' % \
                        (self.instance.__class__.__name__, self.attname))
            elif len(image_fields) > 1:
                raise Exception('%s defines multiple ImageFields, but you' \
                        ' have not specified an image_field for your %s' \
                        ' ImageSpec.' % (self.instance.__class__.__name__,
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
        return self.field.cache_state_backend.clear(self)

    def invalidate(self):
        return self.field.cache_state_backend.invalidate(self)

    def validate(self):
        return self.field.cache_state_backend.validate(self)

    def generate(self, save=True):
        """
        Generates a new image file by processing the source file and returns
        the content of the result, ready for saving.

        """
        source_file = self.source_file
        if source_file:  # TODO: Should we error here or something if the source_file doesn't exist?
            # Process the original image file.
            try:
                fp = source_file.storage.open(source_file.name)
            except IOError:
                return
            fp.seek(0)
            fp = StringIO(fp.read())

            img, content = self._process_content(self.name, fp)

            if save:
                self.storage.save(self.name, content)

            return content

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
        new_name = '%s_%s%s' % (filename, specname, extension)
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

    def __get__(self, instance, owner):
        if instance is None:
            return self.field
        else:
            img_spec_file = ImageSpecFile(instance, self.field, self.attname)
            setattr(instance, self.attname, img_spec_file)
            return img_spec_file


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

    def __init__(self, processors=None, format=None, options={},
        verbose_name=None, name=None, width_field=None, height_field=None,
        autoconvert=True, **kwargs):
        """
        The ProcessedImageField constructor accepts all of the arguments that
        the :class:`django.db.models.ImageField` constructor accepts, as well
        as the ``processors``, ``format``, and ``options`` arguments of
        :class:`imagekit.models.ImageSpec`.

        """
        if 'quality' in kwargs:
            raise Exception('The "quality" keyword argument has been'
                    """ deprecated. Use `options={'quality': %s}` instead.""" \
                    % kwargs['quality'])
        _ImageSpecMixin.__init__(self, processors, format=format,
                options=options, autoconvert=autoconvert)
        models.ImageField.__init__(self, verbose_name, name, width_field,
                height_field, **kwargs)

    def get_filename(self, filename):
        filename = os.path.normpath(self.storage.get_valid_name(os.path.basename(filename)))
        name, ext = os.path.splitext(filename)
        ext = _get_suggested_extension(filename, self.format)
        return '%s%s' % (name, ext)


try:
    from south.modelsinspector import add_introspection_rules
except ImportError:
    pass
else:
    add_introspection_rules([], [r'^imagekit\.models\.ProcessedImageField$'])
