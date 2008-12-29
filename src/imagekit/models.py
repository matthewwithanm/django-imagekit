from datetime import datetime
from django.db import models


class ImageSpec(models.Model):
    pass
    

class SpecAccessor(object):
    def __init__(self, instance, spec):
        self._instance = instance
        self._spec = spec
        
    @property
    def url(self):
        return self._instance._spec_url(spec)
    
    @property
    def path(self):
        return self._instance._spec_path(spec)
        
    @property
    def size(self):
        return self._instance._spec_size(spec)
        
    @property
    def spec(self):


class ImageModel(models.Model):
    """ Abstract base class implementing all core ImageKit functionality
    
    Subclasses of ImageModel can override the inner IKConfig class to customize
    storage locations and other options.
    
    """
    CROP_X_NONE   = 0
    CROP_X_LEFT   = 1
    CROP_X_CENTER = 2
    CROP_X_RIGHT  = 3

    CROP_Y_NONE   = 0
    CROP_Y_TOP    = 1
    CROP_Y_CENTER = 2
    CROP_Y_BOTTOM = 3 

    CROP_X_CHOICES = (
        (CROP_X_NONE, 'None'),
        (CROP_X_LEFT, 'Left'),
        (CROP_X_CENTER, 'Center'),
        (CROP_X_RIGHT, 'Right'),
    )

    CROP_Y_CHOICES = (
        (CROP_Y_NONE, 'None'),
        (CROP_Y_TOP, 'Top'),
        (CROP_Y_CENTER,  'Center'),
        (CROP_Y_BOTTOM, 'Bottom'),
    )

    image = models.ImageField(_('image'), upload_to=get_storage_path)
    crop_x = models.PositiveSmallIntegerField(choices=CROP_X_CHOICES,
                                              default=CROP_X_CENTER)
    crop_y = models.PositiveSmallIntegerField(choices=CROP_Y_CHOICES,
                                              default=CROP_Y_CENTER)

    class Meta:
        abstract = True
        
    class IKConfig:
        """ Contains the default configuration for ImageModel subclasses.
        
        Subclasses can inherit from this class to override configuration 
        options.
        
        """
        max_image_size = (100, 100)
        image_dir = 'image'
        cache_dir = 'cache'
        save_count_as = None # Field name on subclass where count is stored
        cache_filename_format = "%(filename)s_%(specname)s.%(extension)s"
        
    class SpecCache(object):
        """ A pseudo-singleton object that caches ImageSpec instances
        
        Loads all ImageSpecs from the database and caches them to save on the
        total number of queries made.
        
        """
        __state = {"specs": {}}

        def __init__(self):
            self.__dict__ = self.__state
            if not len(self.specs):
                specs = ImageSpec.objects.all()
                for spec in specs:
                    self.specs[spec.name] = spec

        def reset(self):
            self.specs = {}            

    def _image_basename(self):
        """ Returns the basename of the original image file """
        return os.path.basename(self.image.path)

    def _cache_dir(self):
        """ Returns the path to the image cache directory """
        return os.path.join(os.path.dirname(self.image.path), self.IKConfig.cache_dir)

    def _cache_url(self):
        """ Returns a url pointing to the image cache directory """
        return '/'.join([os.path.dirname(self.image.url), self.IKConfig.cache_dir])
        
    def _spec_url(self, spec):
        return '/'.join([self._cache_url(), self._spec_filename(spec)])
        
    def _spec_path(self, spec):
        return os.path.join(self._cache_dir(),
                            self._spec_filename(spec))

    def _spec_filename(self, spec):
        """ Returns a formatted filename for a specific ImageSpec """
        filename, extension = os.path.splitext(self._image_basename())
        return self.IKConfig.cache_filename_format % \
          {'filename': filename,
           'specname': spec.name,
           'extension': extension.lstrip('.')}

    def _increment_view_count(self):
        """ Increment the view count If a field name is supplied in IKConfig """
        field_name = IKConfig.save_count_as
        if field_name is not None:
            new_count = getattr(self, field_name) + 1
            setattr(self, field_name, new_count)
        models.Model.save(self)
        
    def _file_exists(self, spec):
        accessor = getattr(self, spec.name)
        return os.path.isfile(accessor.path)
        
    def _cache_spec(self, spec):
        if self._file_exists(spec):
            return
                        
        # create cache directory if it does not exist
        if not os.path.isdir(self._cache_path()):
            os.makedirs(self._cache_path())
            
        img = Image.open(self.image.path)
        
        if img.size != spec.size and spec.size != (0, 0):
            resized = resize_image(img, spec)
            
        output_filename = self._spec_filename(spec)
        
        try:
            if img.format == 'JPEG':
                resized.save(output_filename, img.format, quality=int(spec.quality))
            else:
                try:
                    im.save(im_filename)
                except KeyError:
                    pass
        except IOError, e:
            if os.path.isfile(output_filename):
                os.unlink(output_filename)
            raise e
            
    def _delete_spec(self, spec, remove_dirs=True):
        if not self._file_exists(spec):
            return
        accessor = getattr(self, spec.name)
        if os.path.isfile(accessor.path):
            os.remove(accessor.path)
        if remove_dirs:
            self._cleanup_cache_dirs
            
    def _cleanup_cache_dirs(self):
        try:
            os.removedirs(self._cache_path())
        except:
            pass

    def _clear_cache(self):
        cache = SpecCache()
        for photosize in cache.sizes.values():
            self._delete_spec(spec, False)
        self._cleanup_cache_dirs()

    def _pre_cache(self):
        cache = SpecCache()
        for spec in cache.specs.values():
            if spec.cache_on_save:
                self._cache_spec(spec)

    def save(self, *args, **kwargs):
        if self._get_pk_val():
            self._clear_cache()
        super(ImageModel, self).save(*args, **kwargs)
        self._pre_cache()

    def delete(self):
        assert self._get_pk_val() is not None, "%s object can't be deleted because its %s attribute is set to None." % (self._meta.object_name, self._meta.pk.attname)
        self._clear_cache()
        super(ImageModel, self).delete()
