import os

from django.core.files.images import ImageFile
from django.db.models.fields.files import ImageFieldFile

from .imagecache import get_default_image_cache_backend
from .generators import SpecFileGenerator
from .processors import ProcessorPipeline, AutoConvert


def autodiscover():
    """
    Auto-discover INSTALLED_APPS imagespecs.py modules and fail silently when
    not present. This forces an import on them to register any admin bits they
    may want.

    Copied from django.contrib.admin
    """

    import copy
    from django.conf import settings
    from django.utils.importlib import import_module
    from django.utils.module_loading import module_has_submodule
    from .templatetags import imagekit_tags

    for app in settings.INSTALLED_APPS:
        mod = import_module(app)
        # Attempt to import the app's admin module.
        try:
            import_module('%s.imagespecs' % app)
        except:
            # Decide whether to bubble up this error. If the app just
            # doesn't have an admin module, we can ignore the error
            # attempting to import it, otherwise we want it to bubble up.
            if module_has_submodule(mod, 'imagespecs'):
                raise


class ImageSpec(object):
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs

    def get_file(self, source_file, spec_id):
        return ImageSpecFile(source_file, spec_id, *self._args, **self._kwargs)
        self.image_cache_backend = getattr(spec, 'image_cache_backend', None) \
                or get_default_image_cache_backend()


class ImageSpecFile(ImageFieldFile):
    def __init__(self, source_file, spec_id, processors=None, format=None, options={},
            autoconvert=True, storage=None, cache_state_backend=None):
        self.generator = SpecFileGenerator(processors=processors,
                format=format, options=options, autoconvert=autoconvert,
                storage=storage)
        self.storage = storage or source_file.storage
        self.cache_state_backend = cache_state_backend or \
                get_default_cache_state_backend()
        self.source_file = source_file
        self.spec_id = spec_id

    @property
    def url(self):
        self.validate()
        return super(ImageFieldFile, self).url

    def _get_file(self):
        self.validate()
        return super(ImageFieldFile, self).file

    file = property(_get_file, ImageFieldFile._set_file, ImageFieldFile._del_file)

    def clear(self):
        return self.cache_state_backend.clear(self)

    def invalidate(self):
        return self.cache_state_backend.invalidate(self)

    def validate(self):
        return self.cache_state_backend.validate(self)

    @property
    def name(self):
        source_filename = self.source_file.name
        filepath, basename = os.path.split(source_filename)
        filename = os.path.splitext(basename)[0]
        extension = self.generator.suggest_extension(source_filename)
        new_name = '%s%s' % (filename, extension)
        cache_filename = ['cache', 'iktt'] + self.spec_id.split(':') + \
                [filepath, new_name]
        return os.path.join(*cache_filename)

    def generate(self, save=True):
        return self.generator.generate_file(self.name, self.source_file, save)
