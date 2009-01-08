""" ImageKit image specifications

All imagekit specifications must inherit from the ImageSpec class. Models
inheriting from IKModel will be modified with a descriptor/accessor for each
spec found.

"""
import os
import tempfile
from imagekit import Image
from django.core.files.base import ContentFile

class ImageSpec(object):
    pre_cache = False
    output_quality = 70
    increment_count = False
    processors = []
    
    @classmethod
    def name(cls):
        return getattr(cls, 'access_as', cls.__name__.lower())
        
    @classmethod
    def process(cls, image):
        processed_image = image.copy()
        for proc in cls.processors:
            processed_image = proc.process(processed_image)
        return processed_image
        

class Accessor(object):
    def __init__(self, obj, spec):
        self._img = None
        self._obj = obj
        self.spec = spec
        
    def _create(self):
        if self._exists():
            return
            
        self._img = self.spec.process(Image.open(self._obj._imgfield.path))

        fmt = self._img.format or 'JPEG'
        tmp = tempfile.TemporaryFile()
        
        try:
            if fmt != 'JPEG':
                try:
                    self._img.save(tmp, fmt)
                    return
                except KeyError:
                    pass
            self._img.save(tmp, fmt,
                           quality=int(self.spec.output_quality),
                           optimize=True)
        except IOError, e:
            self._obj._image.storage.delete(self._path())
        tmp.seek(0)
        content = ContentFile(tmp.read())
        self._obj._imgfield.storage.save(self._path(), content)
        
    def _delete(self):
        self._obj._imgfield.storage.delete(self._path())

    def _exists(self):
        return self._obj._imgfield.storage.exists(self._path())

    def _name(self):
        filename, ext =  os.path.splitext(os.path.basename(self._obj._imgfield.path))
        return self._obj._ik.cache_filename_format % \
            {'filename': filename,
             'specname': self.spec.name(),
             'extension': ext.lstrip('.')}

    def _path(self):
        return os.path.join(self._obj._ik.cache_dir, self._name())

    @property
    def url(self):
        self._create()
        if self.spec.increment_count:
            fieldname = self._obj._ik.save_count_as
            if fieldname is not None:
                current_count = getattr(self._obj, fieldname)
                setattr(self._obj, fieldname, current_count + 1)
        return self._obj._imgfield.storage.url(self._path())
        
    @property
    def file(self):
        self._create()
        return self._obj._imgfield.storage.open(self._path())
        
    @property
    def image(self):
        if self._img is None:
            self._create()
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
