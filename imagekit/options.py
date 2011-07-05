# Imagekit options
import os
from imagekit import processors, specs
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
            self.specs = {}
    
    def clear_cache(self, **kwargs):
        #logg.info('clear_cache() called: %s' % kwargs)
        instance = kwargs.get('instance', None)
        if instance:
            for spec_name, spec in instance._ik.specs.items():
                if spec_name not in ('imagespec', 'spec'):
                    self.delete_spec(instance=instance, spec_name=spec_name)
    
    def pre_cache(self, **kwargs):
        #logg.info('pre_cache() called: %s' % kwargs)
        instance = kwargs.get('instance', None)
        if instance:
            for spec_name, spec in instance._ik.specs.items():
                if spec.pre_cache and spec_name not in ('imagespec', 'spec'):
                    self.prepare_spec(instance=instance, spec_name=spec_name)
    
    def delete_spec(self, **kwargs):
        #logg.info('delete_spec() called: %s' % kwargs)
        instance = kwargs.get('instance', None)
        spec_name = kwargs.get('spec_name', None)
        if instance and spec_name:
            prop = instance.__getattribute__(spec_name)
            prop._delete()
    
    def prepare_spec(self, **kwargs):
        #logg.info('prepare_spec() called: %s' % kwargs)
        instance = kwargs.get('instance', None)
        spec_name = kwargs.get('spec_name', None)
        if instance and spec_name:
            prop = instance.__getattribute__(spec_name)
            prop._create()
    
    def contribute_to_class(self, cls, name):
        signalqueue.pre_cache.connect(self.pre_cache, sender=cls)
        signalqueue.clear_cache.connect(self.clear_cache, sender=cls)
        signalqueue.prepare_spec.connect(self.prepare_spec, sender=cls)
        signalqueue.delete_spec.connect(self.delete_spec, sender=cls)
        
        for spec_name, spec in self.specs.items():
            if issubclass(spec, specs.ImageSpec):
                prop = specs.FileDescriptor(spec)
            elif issubclass(spec, specs.MatrixSpec):
                prop = specs.MatrixDescriptor(spec)
            
            setattr(cls, spec_name, prop)
            cls.add_to_class(spec_name, prop)
        
    
    