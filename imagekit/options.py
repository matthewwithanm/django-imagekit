# Imagekit options
from imagekit import processors
from imagekit.specs import ImageSpec


class Options(object):
    """ Class handling per-model imagekit options

    """
    image_field = 'image'
    crop_horz_field = 'crop_horz'
    crop_vert_field = 'crop_vert'
    preprocessor_spec = None
    cache_dir = 'cache'
    save_count_as = None
    cache_filename_fields = ['pk', ]
    cache_filename_format = "%(filename)s_%(specname)s_%(original_extension)s.%(extension)s"
    admin_thumbnail_spec = 'admin_thumbnail'
    spec_module = 'imagekit.defaults'
    specs = None
    #storage = defaults to image_field.storage

    def __init__(self, opts):
        for key, value in opts.__dict__.iteritems():
            setattr(self, key, value)
        self.specs = list(self.specs or [])
