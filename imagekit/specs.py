""" ImageKit image specifications

All imagekit specifications must inherit from the ImageSpec class. Models
inheriting from ImageModel will be modified with a descriptor/accessor for each
spec found.

"""
import os
import datetime
from StringIO import StringIO
from imagekit import processors
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
        img.format = fmt
        return img, fmt

    def contribute_to_class(self, cls, name):
        setattr(cls, name, Descriptor(self, name))


class Accessor(object):
    def __init__(self, obj, spec, property_name):
        self._img = None
        self._fmt = None
        self._obj = obj
        self.spec = spec
        self.property_name = property_name

    def _get_imgfile(self):
        format = self._img.format or 'JPEG'
        if format != 'JPEG':
            imgfile = img_to_fobj(self._img, format)
        else:
            imgfile = img_to_fobj(self._img, format,
                                  quality=int(self.spec.quality),
                                  optimize=True)
        return imgfile

    @property
    def _imgfield(self):
        return self.spec._get_imgfield(self._obj)

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
            self._img, self._fmt = self.spec.process(Image.open(fp), self._obj)
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
    def name(self):
        filename = self._imgfield.name
        if filename:
            cache_to = getattr(self.spec, 'cache_to', None) or \
                getattr(self._obj._ik, 'default_cache_to', None)

            if not cache_to:
                raise Exception('No cache_to or default_cache_to value specified')
            if callable(cache_to):
                extension = os.path.splitext(filename)[1]
                for processor in self.spec.processors:
                    if isinstance(processor, processors.Format):
                        extension = processor.extension
                new_filename = force_unicode(datetime.datetime.now().strftime( \
                        smart_str(cache_to(self._obj, self._imgfield.name, \
                            self.property_name, extension.lstrip('.')))))
            else:
               dir_name = os.path.normpath(force_unicode(datetime.datetime.now().strftime(smart_str(cache_to))))
               filename = os.path.normpath(os.path.basename(filename))
               new_filename = os.path.join(dir_name, filename)

            return new_filename

    @property
    def _storage(self):
        return getattr(self.spec, 'storage', None) or \
            getattr(self._obj._ik, 'default_storage', None) or \
            self._imgfield.storage

    @property
    def url(self):
        if not self.spec.pre_cache:
            self._create()
        if self.spec.increment_count:
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


class Descriptor(object):
    def __init__(self, spec, property_name):
        self._property_name = property_name
        self._spec = spec

    def __get__(self, obj, type=None):
        return Accessor(obj, self._spec, self._property_name)
