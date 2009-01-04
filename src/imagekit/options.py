# Imagekit options

class Options(object):
    """ Class handling per-model imagekit options

    """
    # Images will be resized to fit if they are larger than max_image_size
    max_image_size = None
    # Media subdirectories
    image_dir_name = 'images'
    cache_dir_name = 'cache'
    # If given the image view count will be saved as this field name
    save_count_as = None
    # String pattern used to generate cache file names
    cache_filename_format = "%(filename)s_%(specname)s.%(extension)s"
    # Configuration options coded in the models itself
    config_module = 'imagekit.config'
    specs = []
    
    def __init__(self, opts):        
        for key, value in opts.__dict__.iteritems():
            setattr(self, key, value)