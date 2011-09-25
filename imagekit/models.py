import os
import datetime
from StringIO import StringIO
from imagekit.lib import *
from imagekit.utils import img_to_fobj, get_spec_files, open_image
from imagekit.processors import ProcessorPipeline
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils.encoding import force_unicode, smart_str
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string
from django.db.models.fields.files import ImageFieldFile


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

    _upload_to_attr = 'cache_to'

    cache_to = None
    """Specifies the filename to use when saving the image cache file. This is
    modeled after ImageField's `upload_to` and can accept either a string
    (that specifies a directory) or a callable (that returns a filepath).
    Callable values should accept the following arguments:

    instance -- the model instance this spec belongs to
    path -- the path of the original image
    specname -- the property name that the spec is bound to on the model instance
    extension -- a recommended extension. If the format of the spec is set
            explicitly, this suggestion will be based on that format. if not,
            the extension of the original file will be passed. You do not have
            to use this extension, it's only a recommendation.

    If you have not explicitly set a format on your ImageSpec, the extension of
    the path returned by this function will be used to infer one.

    """

    def __init__(self, processors=None, quality=70, format=None,
        image_field=None, pre_cache=False, storage=None, cache_to=None):

        _ImageSpecMixin.__init__(self, processors, quality=quality,
                format=format)
        self.image_field = image_field
        self.pre_cache = pre_cache
        self.storage = storage
        self.cache_to = cache_to

    def contribute_to_class(self, cls, name):
        setattr(cls, name, _ImageSpecDescriptor(self, name))
        # Connect to the signals only once for this class.
        uid = '%s.%s' % (cls.__module__, cls.__name__)
        post_save.connect(_post_save_handler,
            sender=cls,
            dispatch_uid='%s_save' % uid)
        post_delete.connect(_post_delete_handler,
            sender=cls,
            dispatch_uid='%s.delete' % uid)


def _get_suggested_extension(name, format):
    if format:
        # Try to look up an extension by the format
        extensions = [k for k, v in Image.EXTENSION.iteritems() \
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
                format = Image.EXTENSION.get(extension)
        format = format or img.format or original_format or 'JPEG'

        if format != 'JPEG':
            imgfile = img_to_fobj(img, format)
        else:
            imgfile = img_to_fobj(img, format,
                                  quality=int(self.field.quality),
                                  optimize=True)
        content = ContentFile(imgfile.read())
        return img, content


class ImageSpecFile(_ImageSpecFileMixin):
    def __init__(self, instance, field, attname, source_file):
        self.field = field
        self._img = None
        self._file = None
        self.instance = instance
        self.attname = attname
        self.source_file = source_file

    def _create(self, lazy=False):
        """Creates a new image by running the processors on the source file.
        
        Keyword Arguments:
        lazy -- True if an already-existing image should be returned; False if
                a new image should be created and the existing one overwritten.

        """
        img = None
        if lazy:
            img = self._img
            if not img and self.storage.exists(self.name):
                img = open_image(self.file)
        if not img and self.source_file:
            # Process the original image file
            try:
                fp = self.source_file.storage.open(self.source_file.name)
            except IOError:
                return
            fp.seek(0)
            fp = StringIO(fp.read())

            img, content = self._process_content(self.name, fp)
            self._file = self.storage.save(self.name, content)
        else:
            # TODO: Should we error here or something if the imagefield doesn't exist?
            img = None
        self._img = img
        return self._img

    def _delete(self):
        if self.source_file:
            try:
                self.storage.delete(self.name)
            except (NotImplementedError, IOError):
                return

    @property
    def _suggested_extension(self):
        return _get_suggested_extension(self.source_file.name, self.field.format)

    def _default_cache_to(self, instance, path, specname, extension):
        """Determines the filename to use for the transformed image. Can be
        overridden on a per-spec basis by setting the cache_to property on the
        spec.

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
        filename = self.source_file.name
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

            return new_filename

    @property
    def storage(self):
        return self.field.storage or self.source_file.storage

    @property
    def url(self):
        if not self.field.pre_cache:
            self._create(True)
        return self.storage.url(self.name)

    @property
    def file(self):
        if not self._file:
            if not self.storage.exists(self.name):
                self._create()
            self._file = self.storage.open(self.name)
        return self._file

    @property
    def image(self):
        return self._create(True)

    @property
    def width(self):
        return self.image.size[0]

    @property
    def height(self):
        return self.image.size[1]


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
            return ImageSpecFile(instance, self.field, self.attname,
                    self._get_image_field_file(instance))


def _post_save_handler(sender, instance=None, created=False, raw=False, **kwargs):
    if raw:
        return
    spec_files = get_spec_files(instance)
    for spec_file in spec_files:
        if not created:
            spec_file._delete()
        if spec_file.field.pre_cache:
            spec_file._create()


def _post_delete_handler(sender, instance=None, **kwargs):
    assert instance._get_pk_val() is not None, "%s object can't be deleted because its %s attribute is set to None." % (instance._meta.object_name, instance._meta.pk.attname)
    spec_files = get_spec_files(instance)
    for spec_file in spec_files:
        spec_file._delete()


class AdminThumbnailView(object):
    short_description = _('Thumbnail')
    allow_tags = True

    def __init__(self, image_field, template=None):
        """
        Keyword arguments:
        image_field -- the name of the ImageField or ImageSpec on the model to
                use for the thumbnail.
        template -- the template with which to render the thumbnail

        """
        self.image_field = image_field
        self.template = template

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            return BoundAdminThumbnailView(instance, self)


class BoundAdminThumbnailView(AdminThumbnailView):
    def __init__(self, model_instance, unbound_field):
        super(BoundAdminThumbnailView, self).__init__(unbound_field.image_field,
                unbound_field.template)
        self.model_instance = model_instance

    def __unicode__(self):
        thumbnail = getattr(self.model_instance, self.image_field, None)
        
        if not thumbnail:
            raise Exception('The property {0} is not defined on {1}.'.format(
                    self.model_instance, self.image_field))

        original_image = getattr(thumbnail, 'source_file', None) or thumbnail
        template = self.template or 'imagekit/admin/thumbnail.html'

        return render_to_string(template, {
            'model': self.model_instance,
            'thumbnail': thumbnail,
            'original_image': original_image,
        })
    
    def __get__(self, instance, owner):
        """Override AdminThumbnailView's implementation."""
        return self


class ProcessedImageFieldFile(ImageFieldFile, _ImageSpecFileMixin):
    def save(self, name, content, save=True):
        new_filename = self.field.generate_filename(self.instance, name)
        img, content = self._process_content(new_filename, content)
        return super(ProcessedImageFieldFile, self).save(name, content, save)


class ProcessedImageField(models.ImageField, _ImageSpecMixin):
    _upload_to_attr = 'upload_to'
    attr_class = ProcessedImageFieldFile

    def __init__(self, processors=None, quality=70, format=None,
        verbose_name=None, name=None, width_field=None, height_field=None,
        **kwargs):

        _ImageSpecMixin.__init__(self, processors, quality=quality,
                format=format)
        models.ImageField.__init__(self, verbose_name, name, width_field,
                height_field, **kwargs)

    def get_filename(self, filename):
        filename = os.path.normpath(self.storage.get_valid_name(os.path.basename(filename)))
        name, ext = os.path.splitext(filename)
        ext = _get_suggested_extension(filename, self.format)
        return '{0}{1}'.format(name, ext)
