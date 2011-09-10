# Imagekit options
from imagekit import processors
from imagekit.specs import ImageSpec


class Options(object):
    """ Class handling per-model imagekit options

    """

    admin_thumbnail_property = 'admin_thumbnail'
    """The name of the spec to be used by the admin_thumbnail_view"""

    default_image_field = None
    """The name of the image field property on the model.
    Can be overridden on a per-spec basis by setting the image_field property on
    the spec. If you don't define default_image_field on your IKOptions class,
    it will be automatically populated with the name of the first ImageField the
    model defines.

    """

    crop_horz_field = 'crop_horz'
    crop_vert_field = 'crop_vert'
    preprocessor_spec = None
    cache_dir = 'cache'
    save_count_as = None
    cache_filename_fields = ['pk', ]
    cache_filename_format = "%(filename)s_%(specname)s.%(extension)s"
    specs = None
    #storage = defaults to image_field.storage

    def __init__(self, opts):
        for key, value in opts.__dict__.iteritems():
            setattr(self, key, value)
        self.specs = list(self.specs or [])
