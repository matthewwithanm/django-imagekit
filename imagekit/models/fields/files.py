from django.db.models.fields.files import ImageFieldFile


class ProcessedImageFieldFile(ImageFieldFile):
    def save(self, name, content, save=True):
        new_filename = self.field.spec.generate_filename(self.instance, name)
        content = self.field.spec.apply(content, new_filename)
        return super(ProcessedImageFieldFile, self).save(name, content, save)
