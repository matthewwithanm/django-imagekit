# Imagekit options
from imagekit import processors
from imagekit.specs import ImageSpec
import os
import os.path


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

    default_storage = None
    """Storage used for specs that don't define their own storage explicitly.
    If neither is specified, the image field's storage will be used.

    """

    def default_cache_to(self, instance, path, specname, extension):
        """Determines the filename to use for the transformed image. Can be
        overridden on a per-spec basis by setting the cache_to property on the
        spec, or on a per-model basis by defining default_cache_to on your own
        IKOptions class.

        """
        filepath, basename = os.path.split(path)
        filename = os.path.splitext(basename)[0]
        new_name = '{0}_{1}.{2}'.format(filename, specname, extension)
        return os.path.join(os.path.join('cache', filepath), new_name)

    crop_horz_field = 'crop_horz'
    crop_vert_field = 'crop_vert'
    preprocessor_spec = None
    save_count_as = None
    specs = None

    def __init__(self, opts):
        for key, value in opts.__dict__.iteritems():
            setattr(self, key, value)
        self.specs = list(self.specs or [])
