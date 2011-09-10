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

    image_field = 'original_image' # TODO: Get rid of this. It can be specified in a SpecDefaults nested class.
    processors = []
    pre_cache = False
    quality = 70
    increment_count = False

    def __init__(self, processors=None, **kwargs):
        if processors:
            self.processors = processors
        self.__dict__.update(kwargs)

    def _get_imgfield(self, obj):
        return getattr(obj, self.image_field)

    def process(self, image, obj):
        fmt = image.format
        img = image.copy()
        for proc in self.processors:
            img, fmt = proc.process(img, fmt, obj, self)
        img.format = fmt
        return img, fmt


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
        if self._imgfield.name:
            filepath, basename = os.path.split(self._imgfield.name)
            filename, extension = os.path.splitext(basename)
            for processor in self.spec.processors:
                if isinstance(processor, processors.Format):
                    extension = processor.extension
            filename_format_dict = {'filename': filename,
                                    'specname': self.property_name,
                                    'extension': extension.lstrip('.')}
            cache_filename_fields = self._obj._ik.cache_filename_fields
            filename_format_dict.update(dict(zip(
                        cache_filename_fields,
                        [getattr(self._obj, field) for
                         field in cache_filename_fields])))
            cache_filename = self._obj._ik.cache_filename_format % \
                filename_format_dict

            if callable(self._obj._ik.cache_dir):
                return self._obj._ik.cache_dir(self._obj, filepath,
                                               cache_filename)
            else:
                return os.path.join(self._obj._ik.cache_dir, filepath,
                                    cache_filename)

    @property
    def _storage(self):
        return getattr(self._obj._ik, 'storage', self._imgfield.storage)

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
