""" ImageKit image specifications

All imagekit specifications must inherit from the ImageSpec class. Models
inheriting from IKModel will be modified with a descriptor/accessor for each
spec found.

"""
class ImageSpec(object):
    cache_on_save = False
    output_quality = 70
    increment_count = False
    processors = []
    
    @property
    @classmethod
    def name(cls):
        return getattr(cls, 'access_as', cls.__name__.lower())
        
    @classmethod
    def process(cls, image, save_as=None):
        processed_image = image.copy()
        for proc in cls.processors:
            processed_image = proc.process(processed_image)
            
        if save_as is not None:
            try:
                if image.format != 'JPEG':
                    try:
                        processed_image.save(save_as)
                        return
                    except KeyError:
                        pass
                processed_image.save(save_as, 'JPEG',
                                     quality=int(cls.output_quality),
                                     optimize=True)
            except IOError, e:
                if os.path.isfile(filename):
                    os.unlink(filename)
                raise e
        
        return processed_image
        

class Accessor(object):
    def __init__(self, obj, spec):
        self._img = None
        self._obj = obj
        self.spec = spec
        
    def create(self):
        self._img = self.spec.process(self.image, save_as=self.path)
        
    def delete(self):
        if self.exists:
            os.remove(self.path)
        self._img = None
        
    @property
    def name(self):
        filename, ext = os.path.splitext(os.path.basename(self._obj.image.path))
        return self.spec._ik.cache_filename_format % \
            {'filename': filename,
             'sizename': self.spec.name,
             'extension': ext.lstrip('.')}
             
    @property
    def path(self):
        return os.abspath(os.path.join(self._obj.cache_dir, self.name)

    @property
    def url(self):
        if not self.exists:
            self.create()
        if self.spec.increment_count():
            fieldname = self._obj._ik.save_count_as
            if fieldname is not None:
                current_count = getattr(self._obj, fieldname)
                setattr(self._obj, fieldname, current_count + 1)
        return '/'.join([self._obj.cache_url, self.name])
        
    @property
    def exists(self):
        return os.path.isfile(self.path)
        
    @property
    def image(self):
        if self._img is None:
            if not self.exists():
                self.create()
            else:
                self._img = Image.open(self.path)
        return self._img
        
    @property
    def width(self):
        return self.image.size[0]
        
    @property
    def height(self):
        return self.image.size[1]
        
    @property
    def file(self):
        if not self.exists:
            self.create()
        return open(self.path)


class Descriptor(object):
    def __init__(self, spec):
        self._spec = spec
        self._prop = None

    def __get__(self, obj, type=None):
        if self._prop is None:
            self._prop = Accessor(obj, self._spec)
        return self._prop
