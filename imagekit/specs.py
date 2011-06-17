""" ImageKit image specifications

All imagekit specifications must inherit from the ImageSpec class. Models
inheriting from ImageModel will be modified with a descriptor/accessor for each
spec found.

"""

import os, warnings, numpy
from StringIO import StringIO
from imagekit import processors
from imagekit.lib import *
from imagekit.utils import img_to_fobj
from imagekit.memoize import memoize
from django.core.files.base import ContentFile

matrixlike = (numpy.matrixlib.matrix, numpy.ndarray)

class Spec(object):
    pre_cache = False
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
        return img, fmt

class ImageSpec(Spec):
    quality = 70
    
    @classmethod
    def process(cls, image, obj):
        img, fmt = super(ImageSpec, cls).process(image, obj)
        img.format = fmt
        return img, fmt

class MatrixSpec(Spec):
    shape = None
    dtype = None
    cache = False # for now




class AccessorBase(object):
    def __init__(self, obj, spec, **kwargs):
        self._img = None
        self._fmt = None
        self._obj = obj
        self.spec = spec
        ImageFile.MAXBLOCK = 1024*1024

class MatrixAccessor(AccessorBase):
    def __init__(self, obj, spec, **kwargs):
        super(MatrixAccessor, self).__init__(obj, spec, **kwargs)
    
    @memoize
    def _get_matrixdata(self):
        mat = self._img
        format = getattr(mat, "format", None) or 'array'
        if not isinstance(mat, matrixlike):
            mat = numpy.array(mat)
        if self.spec.dtype:
            if not issubclass(mat.dtype, self.spec.dtype):
                mat = mat.astype(self.spec.dtype)
        if self.spec.shape:
            mat = mat.reshape(self.spec.shape)
        return mat
    
    def _create(self):
        if self._obj._imgfield:
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
            # save the output matrix
            self.data = self._get_matrixdata()
        
    def _delete(self):
        if self._obj._imgfield:
            if self._exists():
                del self._data
    
    def _exists(self):
        if self._obj._imgfield:
            if self.name:
                return hasattr(self, _data)
    
    @property
    def name(self):
        # caching goes here.
        return self._obj._imgfield.name
    
    @memoize
    def getdata(self):
        self._create()
        if self._exists():
            return getattr(self, "_data", None)
    
    def setdata(self, d):
        self._data = d
    
    data = property(getdata, setdata)
    

class FileAccessor(AccessorBase):
    def __init__(self, obj, spec, **kwargs):
        super(FileAccessor, self).__init__(obj, spec, **kwargs)
    
    def _get_imgfile(self):
        format = self._img.format or 'JPEG'
        if format != 'JPEG':
            imgfile = img_to_fobj(self._img, format)
        else:
            try:
                imgfile = img_to_fobj(self._img, format, quality=int(self.spec.quality), optimize=True)
            except IOError:
                warnings.warn('---\t saving at quality %s (non-optimized) raised IOError' % int(self.spec.quality))
                try:
                    imgfile = img_to_fobj(self._img, format, quality=70, optimize=True)
                except IOError:
                    warnings.warn('---\t saving at quality 70 (optimized) raised IOError' % int(self.spec.quality))
                    imgfile = img_to_fobj(self._img, format, quality=70)
        return imgfile
    
    def _create(self):
        if self._obj._imgfield:
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
        if self._obj._imgfield:
            if self._exists():
                self._obj._storage.delete(self.name)
    
    def _exists(self):
        if self._obj._imgfield:
            if self.name:
                return self._obj._storage.exists(self.name)
    
    @property
    def name(self):
        nn = self._obj._imgfield.name
        if nn:
            filepath, basename = os.path.split(str(nn))
            filename, extension = os.path.splitext(basename)
            
            for processor in self.spec.processors:
                if issubclass(processor, processors.Format):
                    extension = processor.extension
            
            cache_filename = self._obj._ik.cache_filename_format % {
                'filename': filename,
                'specname': self.spec.name(),
                'extension': extension.lstrip('.'),
            }
            
            if callable(self._obj._ik.cache_dir):
                return self._obj._ik.cache_dir(self._obj, filepath, cache_filename)
            else:
                return os.path.join(self._obj._ik.cache_dir, filepath, cache_filename)

    @property
    def url(self):
        if not self.spec.pre_cache:
            self._create()
        
        '''
        if self.spec.increment_count:
            fieldname = self._obj._ik.save_count_as
            if fieldname is not None:
                current_count = getattr(self._obj, fieldname)
                setattr(self._obj, fieldname, current_count + 1)
                self._obj.save(clear_cache=False)
        '''
        return self._obj._storage.url(self.name)
    
    @property
    def file(self):
        self._create()
        if self._exists():
            return self._obj._storage.open(self.name)
    
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


class FileDescriptor(object):
    def __init__(self, spec):
        self._spec = spec
    
    def __get__(self, obj, type=None):
        return FileAccessor(obj, self._spec)


class MatrixDescriptor(object):
    def __init__(self, spec):
        self._spec = spec

    def __get__(self, obj, type=None):
        return MatrixAccessor(obj, self._spec)

