from django.db.models.fields.files import ImageFieldFile
import os
from ...utils import suggest_extension


class ProcessedImageFieldFile(ImageFieldFile):
    def save(self, name, content, save=True):
        filename, ext = os.path.splitext(name)
        spec = self.field.get_spec()  # TODO: What "hints"?
        ext = suggest_extension(name, spec.format)
        new_name = '%s%s' % (filename, ext)
        content = spec.apply(content, new_name)
        return super(ProcessedImageFieldFile, self).save(new_name, content, save)
