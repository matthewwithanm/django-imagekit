# Imagekit options

class Options(object):
    """ Class handling per-model imagekit options

    """
    image_field = 'image'
    max_image_size = None
    cache_dir = 'ik_cache'
    save_count_as = None
    cache_filename_format = "%(filename)s_%(specname)s.%(extension)s"
    config_module = 'imagekit.config'
    
    def __init__(self, opts):        
        for key, value in opts.__dict__.iteritems():
            setattr(self, key, value)
            self.specs = []