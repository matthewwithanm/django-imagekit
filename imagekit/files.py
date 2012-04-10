import os

from django.db.models.fields.files import ImageFieldFile

from .generators import SpecFileGenerator
from .utils import SpecWrapper


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
