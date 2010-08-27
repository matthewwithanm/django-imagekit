""" ImageKit image specifications

All imagekit specifications must inherit from the ImageSpec class. Models
inheriting from ImageModel will be modified with a descriptor/accessor for each
spec found.

"""
import os
from StringIO import StringIO
from imagekit import processors
from imagekit.lib import *
from imagekit.utils import img_to_fobj
from django.core.files.base import ContentFile


class ImageSpec(object):
    pre_cache = False
    quality = 70
    increment_count = False
    processors = []

    @classmethod
    def name(cls):
        return getattr(cls, 'access_as', cls.__name__.lower())

    @classmethod
    def process(cls, image, obj):
        fmt = image.format
        img = image.copy()
        for proc in cls.processors:
            img, fmt = proc.process(img, fmt, obj)
        img.format = fmt
        return img, fmt


class Accessor(object):
    def __init__(self, obj, spec):
        self._img = None
        self._fmt = None
        self._obj = obj
        self.spec = spec

    def _get_imgfile(self):
        format = self._img.format or 'JPEG'
        if format != 'JPEG':
            imgfile = img_to_fobj(self._img, format)
        else:
            imgfile = img_to_fobj(self._img, format,
                                  quality=int(self.spec.quality),
                                  optimize=True)
        return imgfile

    def _create(self):
        if self._exists():
            return
        # process the original image file
        try:
            fp = self._obj._imgfield.storage.open(self._obj._imgfield.name)
        except IOError:
            return
        fp.seek(0)
        fp = StringIO(fp.read())
        self._img, self._fmt = self.spec.process(Image.open(fp), self._obj)
        # save the new image to the cache
        content = ContentFile(self._get_imgfile().read())
        self._obj._storage.save(self.name, content)

    def _delete(self):
        self._obj._storage.delete(self.name)

    def _exists(self):
        return self._obj._storage.exists(self.name)

    @property
    def name(self):
        filepath, basename = os.path.split(self._obj._imgfield.name)
        filename, extension = os.path.splitext(basename)
        for processor in self.spec.processors:
            if issubclass(processor, processors.Format):
                extension = processor.extension
        cache_filename = self._obj._ik.cache_filename_format % \
            {'filename': filename,
             'specname': self.spec.name(),
             'extension': extension.lstrip('.')}
        if callable(self._obj._ik.cache_dir):
            return self._obj._ik.cache_dir(self._obj, filepath,
                                           cache_filename)
        else:
            return os.path.join(self._obj._ik.cache_dir, filepath,
                                cache_filename)

    @property
    def url(self):
        self._create()
        if self.spec.increment_count:
            fieldname = self._obj._ik.save_count_as
            if fieldname is not None:
                current_count = getattr(self._obj, fieldname)
                setattr(self._obj, fieldname, current_count + 1)
                self._obj.save(clear_cache=False)
        return self._obj._storage.url(self.name)

    @property
    def file(self):
        self._create()
        return self._obj._storage.open(self.name)

    @property
    def image(self):
        if self._img is None:
            self._create()
            if self._img is None:
                self._img = Image.open(self.file)
        return self._img

    @property
    def width(self):
        return self.image.size[0]

    @property
    def height(self):
        return self.image.size[1]


class Descriptor(object):
    def __init__(self, spec):
        self._spec = spec

    def __get__(self, obj, type=None):
        return Accessor(obj, self._spec)
