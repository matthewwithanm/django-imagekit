import os

from django.db.models.fields.files import ImageFieldFile

from ...utils import generate, suggest_extension


class ProcessedImageFieldFile(ImageFieldFile):
    def save(self, name, content, save=True):
        filename, ext = os.path.splitext(name)
        spec = self.field.get_spec(source=content)
        ext = suggest_extension(name, spec.format)
        new_name = '%s%s' % (filename, ext)
        content = generate(spec)
        # Django needs a named file to update the model's dimension fields.
        content.name = new_name
        return super().save(new_name, content, save)
