""" ImageKit image specifications

All imagekit specifications must inherit from the ImageSpec class. Models
inheriting from ImageModel will be modified with a descriptor/accessor for each
spec found.

"""
import os
import datetime
from StringIO import StringIO
from imagekit.lib import *
from imagekit.utils import img_to_fobj
from django.core.files.base import ContentFile
from django.utils.encoding import force_unicode, smart_str


class ImageSpec(object):

    image_field = None
    processors = []
    pre_cache = False
    quality = 70
    increment_count = False
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

    def _get_imgfield(self, obj):
        field_name = getattr(self, 'image_field', None) or obj._ik.default_image_field
        return getattr(obj, field_name)

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


class BoundImageSpec(ImageSpec):
    def __init__(self, obj, unbound_field, property_name):
        super(BoundImageSpec, self).__init__(unbound_field.processors,
                image_field=unbound_field.image_field,
                pre_cache=unbound_field.pre_cache,
                quality=unbound_field.quality,
                increment_count=unbound_field.increment_count,
                storage=unbound_field.storage, format=unbound_field.format,
                cache_to=unbound_field.cache_to)
        self._img = None
        self._fmt = None
        self._obj = obj
        self.property_name = property_name

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
        return self._get_imgfield(self._obj)

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

    @property
    def name(self):
        """
        Specifies the filename that the cached image will use. The user can
        control this by providing a `cache_to` method to the ImageSpec.

        """
        filename = self._imgfield.name
        if filename:
            cache_to = self.cache_to or \
                getattr(self._obj._ik, 'default_cache_to', None)

            if not cache_to:
                raise Exception('No cache_to or default_cache_to value specified')
            if callable(cache_to):
                new_filename = force_unicode(datetime.datetime.now().strftime( \
                        smart_str(cache_to(self._obj, self._imgfield.name, \
                            self.property_name, self._suggested_extension))))
            else:
               dir_name = os.path.normpath(force_unicode(datetime.datetime.now().strftime(smart_str(cache_to))))
               filename = os.path.normpath(os.path.basename(filename))
               new_filename = os.path.join(dir_name, filename)

            return new_filename

    @property
    def _storage(self):
        return self.storage or \
            getattr(self._obj._ik, 'default_storage', None) or \
            self._imgfield.storage

    @property
    def url(self):
        if not self.pre_cache:
            self._create()
        if self.increment_count:
            fieldname = self._obj._ik.save_count_as
            if fieldname is not None:
                current_count = getattr(self._obj, fieldname)
                setattr(self._obj, fieldname, current_count + 1)
                self._obj.save(clear_cache=False)
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
    def __init__(self, spec, property_name):
        self._property_name = property_name
        self._spec = spec

    def __get__(self, obj, type=None):
        return BoundImageSpec(obj, self._spec, self._property_name)
