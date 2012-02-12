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


class SpecWrapper(object):
    """
    Wraps a user-defined spec object so we can access properties that don't
    exist without errors.

    """
    def __init__(self, spec):
        self.processors = getattr(spec, 'processors', None)
        self.format = getattr(spec, 'format', None)
        self.options = getattr(spec, 'options', None)
        self.autoconvert = getattr(spec, 'autoconvert', True)
        self.storage = getattr(spec, 'storage', None)
        self.image_cache_backend = getattr(spec, 'image_cache_backend', None) \
                or get_default_image_cache_backend()


class ImageSpecFile(ImageFieldFile):
    def __init__(self, spec, source_file, spec_id):
        spec = SpecWrapper(spec)

        self.storage = spec.storage or source_file.storage
        self.generator = SpecFileGenerator(processors=spec.processors,
                format=spec.format, options=spec.options,
                autoconvert=spec.autoconvert, storage=self.storage)

        self.spec = spec
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
        return self.spec.image_cache_backend.clear(self)

    def invalidate(self):
        return self.spec.image_cache_backend.invalidate(self)

    def validate(self):
        return self.spec.image_cache_backend.validate(self)

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
