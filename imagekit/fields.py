import os
import datetime
from StringIO import StringIO
from imagekit.lib import *
from imagekit.utils import img_to_fobj, get_bound_specs
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils.encoding import force_unicode, smart_str
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string


# Modify image file buffer size.
ImageFile.MAXBLOCK = getattr(settings, 'PIL_IMAGEFILE_MAXBLOCK', 256 * 2 ** 10)


class ImageSpec(object):

    image_field = None
    processors = []
    pre_cache = False
    quality = 70
    storage = None
    format = None

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

    def __init__(self, processors=None, **kwargs):
        if processors:
            self.processors = processors
        self.__dict__.update(kwargs)

    def process(self, image, obj):
        fmt = image.format
        img = image.copy()
        for proc in self.processors:
            img, fmt = proc.process(img, fmt, obj, self)
        format = self.format or fmt
        img.format = format
        return img, format

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


class BoundImageSpec(ImageSpec):
    def __init__(self, obj, unbound_field, attname):
        super(BoundImageSpec, self).__init__(unbound_field.processors,
                image_field=unbound_field.image_field,
                pre_cache=unbound_field.pre_cache,
                quality=unbound_field.quality,
                storage=unbound_field.storage, format=unbound_field.format,
                cache_to=unbound_field.cache_to)
        self._img = None
        self._fmt = None
        self._obj = obj
        self.attname = attname

    @property
    def _format(self):
        """The format used to save the cache file. If the format is set
        explicitly on the ImageSpec, that format will be used. Otherwise, the
        format will be inferred from the extension of the cache filename (see
        the `name` property).

        """
        format = self.format
        if not format:
            # Get the real (not suggested) extension.
            extension = os.path.splitext(self.name)[1].lower()
            # Try to guess the format from the extension.
            format = Image.EXTENSION.get(extension)
        return format or self._img.format or 'JPEG'

    def _get_imgfile(self):
        format = self._format
        if format != 'JPEG':
            imgfile = img_to_fobj(self._img, format)
        else:
            imgfile = img_to_fobj(self._img, format,
                                  quality=int(self.quality),
                                  optimize=True)
        return imgfile

    @property
    def _imgfield(self):
        field_name = getattr(self, 'image_field', None)
        if field_name:
            field = getattr(self._obj, field_name)
        else:
            image_fields = [getattr(self._obj, f.attname) for f in \
                    self._obj.__class__._meta.fields if \
                    isinstance(f, models.ImageField)]
            if len(image_fields) == 0:
                raise Exception('{0} does not define any ImageFields, so your '
                        '{1} ImageSpec has no image to act on.'.format(
                        self._obj.__class__.__name__, self.attname))
            elif len(image_fields) > 1:
                raise Exception('{0} defines multiple ImageFields, but you have '
                        'not specified an image_field for your {1} '
                        'ImageSpec.'.format(self._obj.__class__.__name__,
                        self.attname))
            else:
                field = image_fields[0]
        return field

    def _create(self):
        if self._imgfield:
            if self._exists():
                return
            # process the original image file
            try:
                fp = self._imgfield.storage.open(self._imgfield.name)
            except IOError:
                return
            fp.seek(0)
            fp = StringIO(fp.read())
            self._img, self._fmt = self.process(Image.open(fp), self._obj)
            # save the new image to the cache
            content = ContentFile(self._get_imgfile().read())
            self._storage.save(self.name, content)

    def _delete(self):
        if self._imgfield:
            try:
                self._storage.delete(self.name)
            except (NotImplementedError, IOError):
                return

    def _exists(self):
        if self._imgfield:
            return self._storage.exists(self.name)

    @property
    def _suggested_extension(self):
        if self.format:
            # Try to look up an extension by the format
            extensions = [k.lstrip('.') for k, v in Image.EXTENSION.iteritems() \
                    if v == self.format.upper()]
        else:
            extensions = []
        original_extension = os.path.splitext(self._imgfield.name)[1].lstrip('.')
        if not extensions or original_extension.lower() in extensions:
            # If the original extension matches the format, use it.
            extension = original_extension
        else:
            extension = extensions[0]
        return extension

    def _default_cache_to(self, instance, path, specname, extension):
        """Determines the filename to use for the transformed image. Can be
        overridden on a per-spec basis by setting the cache_to property on the
        spec.

        """
        filepath, basename = os.path.split(path)
        filename = os.path.splitext(basename)[0]
        new_name = '{0}_{1}.{2}'.format(filename, specname, extension)
        return os.path.join(os.path.join('cache', filepath), new_name)

    @property
    def name(self):
        """
        Specifies the filename that the cached image will use. The user can
        control this by providing a `cache_to` method to the ImageSpec.

        """
        filename = self._imgfield.name
        if filename:
            cache_to = self.cache_to or self._default_cache_to

            if not cache_to:
                raise Exception('No cache_to or default_cache_to value specified')
            if callable(cache_to):
                new_filename = force_unicode(datetime.datetime.now().strftime( \
                        smart_str(cache_to(self._obj, self._imgfield.name, \
                            self.attname, self._suggested_extension))))
            else:
               dir_name = os.path.normpath(force_unicode(datetime.datetime.now().strftime(smart_str(cache_to))))
               filename = os.path.normpath(os.path.basename(filename))
               new_filename = os.path.join(dir_name, filename)

            return new_filename

    @property
    def _storage(self):
        return self.storage or self._imgfield.storage

    @property
    def url(self):
        if not self.pre_cache:
            self._create()
        return self._storage.url(self.name)

    @property
    def file(self):
        self._create()
        return self._storage.open(self.name)

    @property
    def image(self):
        if not self._img:
            self._create()
            if not self._img:
                self._img = Image.open(self.file)
        return self._img

    @property
    def width(self):
        return self.image.size[0]

    @property
    def height(self):
        return self.image.size[1]


class _ImageSpecDescriptor(object):
    def __init__(self, spec, attname):
        self._attname = attname
        self._spec = spec

    def __get__(self, instance, owner):
        if instance is None:
            return self._spec
        else:
            return BoundImageSpec(instance, self._spec, self._attname)


def _post_save_handler(sender, instance=None, created=False, raw=False, **kwargs):
    if raw:
        return
    bound_specs = get_bound_specs(instance)
    for bound_spec in bound_specs:
        name = bound_spec.attname
        imgfield = bound_spec._imgfield
        if imgfield:
            newfile = imgfield.storage.open(imgfield.name)
            img = Image.open(newfile)
            img, format = bound_spec.process(img, instance)
            if format != 'JPEG':
                imgfile = img_to_fobj(img, format)
            else:
                imgfile = img_to_fobj(img, format,
                                      quality=int(bound_spec.quality),
                                      optimize=True)
            content = ContentFile(imgfile.read())
            newfile.close()
            name = str(imgfield)
            imgfield.storage.delete(name)
            imgfield.storage.save(name, content)
            if not created:
                bound_spec._delete()
                bound_spec._create()


def _post_delete_handler(sender, instance=None, **kwargs):
    assert instance._get_pk_val() is not None, "%s object can't be deleted because its %s attribute is set to None." % (instance._meta.object_name, instance._meta.pk.attname)
    bound_specs = get_bound_specs(instance)
    for bound_spec in bound_specs:
        bound_spec._delete()


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

        original_image = getattr(thumbnail, '_imgfield', None) or thumbnail
        template = self.template or 'imagekit/admin/thumbnail.html'

        return render_to_string(template, {
            'model': self.model_instance,
            'thumbnail': thumbnail,
            'original_image': original_image,
        })
    
    def __get__(self, instance, owner):
        """Override AdminThumbnailView's implementation."""
        return self
