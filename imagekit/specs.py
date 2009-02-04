""" ImageKit image specifications

All imagekit specifications must inherit from the ImageSpec class. Models
inheriting from ImageModel will be modified with a descriptor/accessor for each
spec found.

"""
import os
from StringIO import StringIO
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
        processed_image = image.copy()
        for proc in cls.processors:
            processed_image = proc.process(processed_image, obj)
        return processed_image
        

class Accessor(object):
    def __init__(self, obj, spec):
        self._img = None
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
        fp = self._obj._imgfield.storage.open(self._obj._imgfield.name)
        fp.seek(0)
        fp = StringIO(fp.read())
        self._img = self.spec.process(Image.open(fp), self._obj)
        # save the new image to the cache
        content = ContentFile(self._get_imgfile().read())
        self._obj._imgfield.storage.save(self.name, content)
        
    def _delete(self):
        self._obj._imgfield.storage.delete(self.name)

    def _exists(self):
        return self._obj._imgfield.storage.exists(self.name)

    def _basename(self):
        filename, extension =  \
            os.path.splitext(os.path.basename(self._obj._imgfield.name))
        return self._obj._ik.cache_filename_format % \
            {'filename': filename,
             'specname': self.spec.name(),
             'extension': extension.lstrip('.')}

    @property
    def name(self):
        return os.path.join(self._obj._ik.cache_dir, self._basename())

    @property
    def url(self):
        self._create()
        if self.spec.increment_count:
            fieldname = self._obj._ik.save_count_as
            if fieldname is not None:
                current_count = getattr(self._obj, fieldname)
                setattr(self._obj, fieldname, current_count + 1)
                self._obj.save(clear_cache=False)
        return self._obj._imgfield.storage.url(self.name)
        
    @property
    def file(self):
        self._create()
        return self._obj._imgfield.storage.open(self.name)
        
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
