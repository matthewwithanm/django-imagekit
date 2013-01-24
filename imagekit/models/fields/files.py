from django.db.models.fields.files import ImageFieldFile
import os
from ...utils import suggest_extension, generate


class ProcessedImageFieldFile(ImageFieldFile):
    def save(self, name, content, save=True):
        filename, ext = os.path.splitext(name)
        spec = self.field.get_spec(source=content)
        ext = suggest_extension(name, spec.format)
        new_name = '%s%s' % (filename, ext)
        content = generate(spec)
        return super(ProcessedImageFieldFile, self).save(new_name, content, save)
