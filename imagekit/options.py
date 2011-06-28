# Imagekit options
import os
from imagekit import processors
from imagekit.specs import ImageSpec
from imagekit.signals import signalqueue
from imagekit.utils import logg


class Options(object):
    """
    Class handling per-model imagekit options
    """
    image_field = 'image'
    crop_horz_field = 'crop_horz'
    crop_vert_field = 'crop_vert'
    preprocessor_spec = None
    cache_dir = 'cache'
    
    enable_metadata = False
    icc_dir = None # setting icc_dir enables icc processing
    icc_field = None
    
    save_count_as = None
    cache_filename_format = "%(filename)s_%(specname)s.%(extension)s"
    admin_thumbnail_spec = 'admin_thumbnail'
    spec_module = 'imagekit.defaults'
    #storage = defaults to image_field.storage

    def __init__(self, opts):
        for key, value in opts.__dict__.iteritems():
            setattr(self, key, value)
            self.specs = []
    
    def _clear_cache(self, **kwargs):
        logg.info('_clear_cache() called: %s' % kwargs)
        instance = kwargs.get('instance', None)
        if instance:
            for spec in instance._ik.specs:
                prop = getattr(instance, spec.name())
                prop._delete()
    
    def _pre_cache(self, **kwargs):
        logg.info('_pre_cache() called: %s' % kwargs)
        instance = kwargs.get('instance', None)
        if instance:
            for spec in instance._ik.specs:
                if spec.pre_cache:
                    prop = getattr(instance, spec.name())
                    prop._create()
    
    def contribute_to_class(self, cls, name):
        #if not cls._meta.abstract:
        signalqueue.pre_cache.connect(self._pre_cache, sender=cls)
        signalqueue.clear_cache.connect(self._clear_cache, sender=cls)
        
        
    
    