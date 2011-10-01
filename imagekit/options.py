# Imagekit options
from imagekit import specs
from imagekit import signals as iksignals
#from imagekit.utils import logg


class Options(object):
    """
    Encapsulation of per-model imagekit options.
    
    """
    image_field = 'image'
    crop_horz_field = 'crop_horz'
    crop_vert_field = 'crop_vert'
    preprocessor_spec = None
    cache_dir = 'cache'
    proof_dir = 'proofs'
    
    save_count_as = None
    cache_filename_format = "%(filename)s_%(specname)s.%(extension)s"
    admin_thumbnail_spec = 'admin_thumbnail'
    spec_module = 'imagekit.defaults'
    
    def __init__(self, opts):
        for key, value in opts.__dict__.iteritems():
            setattr(self, key, value)
            self.specs = {}
    
    def update(self, opts):
        for key, value in opts.__dict__.iteritems():
            setattr(self, key, value)
    
    def clear_cache(self, **kwargs):
        #logg.info('clear_cache() called: %s' % kwargs)
        instance = kwargs.get('instance', None)
        if instance:
            for spec_name, spec in instance._ik.specs.items():
                if spec_name not in ('imagespec', 'spec', None):
                    self.delete_spec(instance=instance, spec_name=spec_name)
    
    def pre_cache(self, **kwargs):
        #logg.info('pre_cache() called: %s' % kwargs)
        instance = kwargs.get('instance', None)
        if instance:
            for spec_name, spec in instance._ik.specs.items():
                if spec.pre_cache and spec_name not in ('imagespec', 'spec', None):
                    self.prepare_spec(instance=instance, spec_name=spec_name)
    
    def delete_spec(self, **kwargs):
        #logg.info('delete_spec() called: %s' % kwargs)
        instance = kwargs.get('instance', None)
        spec_name = kwargs.get('spec_name', None)
        if instance and spec_name:
            #prop = instance._ik._props.get(spec_name).accessor(instance, self.specs[spec_name])
            iksignals.delete_spec.send_now(sender=instance.__class__, instance=instance, spec_name=spec_name)
    
    def prepare_spec(self, **kwargs):
        #logg.info('prepare_spec() called: %s' % kwargs)
        instance = kwargs.get('instance', None)
        spec_name = kwargs.get('spec_name', None)
        #spec = kwargs.get('spec', None)
        if instance and spec_name:
            prop = instance._ik._props.get(spec_name).accessor(instance, self.specs[spec_name])
            if not instance._storage.exists(prop.name):
                iksignals.prepare_spec.send(sender=instance.__class__, instance=instance, spec_name=spec_name)
    
    def contribute_to_class(self, cls, name):
        self._props = {}
        for spec_name, spec in self.specs.items():
            if issubclass(spec, specs.ImageSpec):
                prop = specs.FileDescriptor(spec)
            elif issubclass(spec, specs.MatrixSpec):
                prop = specs.MatrixDescriptor(spec)
            
            self._props[spec_name] = prop
            setattr(cls, spec_name, prop)
            cls.add_to_class(spec_name, prop)
        
        iksignals.pre_cache.connect(self.pre_cache, sender=cls, dispatch_uid="imagekit-options-pre-cache")
        iksignals.clear_cache.connect(self.clear_cache, sender=cls, dispatch_uid="imagekit-options-clear-cache")
        iksignals.prepare_spec.connect(self.do_prepare_spec, sender=cls, dispatch_uid="imagekit-options-prepare-spec")
        iksignals.delete_spec.connect(self.do_delete_spec, sender=cls, dispatch_uid="imagekit-options-delete-spec")
    
    def do_delete_spec(self, **kwargs):
        instance = kwargs.get('instance', None)
        spec_name = kwargs.get('spec_name', None)
        #logg.info('do_delete_spec() called -- instance: %s, spec_name: %s' % (instance, spec_name))
        prop = instance._ik._props.get(spec_name).accessor(instance, self.specs[spec_name])
        if prop is not None:
            prop._delete()
    
    def do_prepare_spec(self, **kwargs):
        instance = kwargs.get('instance', None)
        spec_name = kwargs.get('spec_name', None)
        #logg.info('do_prepare_spec() called -- instance: %s, spec_name: %s' % (instance, spec_name))
        prop = instance._ik._props.get(spec_name).accessor(instance, self.specs[spec_name])
        if prop is not None:
            prop._create()
    