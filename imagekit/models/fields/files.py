from django.db.models.fields.files import ImageFieldFile


class ProcessedImageFieldFile(ImageFieldFile):
    def save(self, name, content, save=True):
        new_filename = self.field.spec.generate_filename(self.instance, name)
        img, content = self.field.spec.process_content(content,
                new_filename, self)
        return super(ProcessedImageFieldFile, self).save(name, content, save)
