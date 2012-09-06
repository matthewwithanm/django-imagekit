from django.db.models.fields.files import ImageField, ImageFieldFile


class ImageSpecFieldFile(ImageFieldFile):
    def __init__(self, instance, field, attname):
        super(ImageSpecFieldFile, self).__init__(instance, field, None)
        self.attname = attname

    @property
    def source_file(self):
        field_name = getattr(self.field, 'image_field', None)
        if field_name:
            field_file = getattr(self.instance, field_name)
        else:
            image_fields = [getattr(self.instance, f.attname) for f in \
                    self.instance.__class__._meta.fields if \
                    isinstance(f, ImageField)]
            if len(image_fields) == 0:
                raise Exception('%s does not define any ImageFields, so your' \
                        ' %s ImageSpecField has no image to act on.' % \
                        (self.instance.__class__.__name__, self.attname))
            elif len(image_fields) > 1:
                raise Exception('%s defines multiple ImageFields, but you' \
                        ' have not specified an image_field for your %s' \
                        ' ImageSpecField.' % (self.instance.__class__.__name__,
                        self.attname))
            else:
                field_file = image_fields[0]
        return field_file

    def _require_file(self):
        if not self.source_file:
            raise ValueError("The '%s' attribute's image_field has no file associated with it." % self.attname)
        elif self.field.validate_on_access:
            self.validate()

    def clear(self):
        return self.field.image_cache_backend.clear(self)

    def invalidate(self):
        return self.field.image_cache_backend.invalidate(self)

    def validate(self):
        return self.field.image_cache_backend.validate(self)

    def generate(self, save=True):
        """
        Generates a new image file by processing the source file and returns
        the content of the result, ready for saving.

        """
        return self.field.generator.generate_file(self.name, self.source_file,
                save)

    def delete(self, save=False):
        """
        Pulled almost verbatim from ``ImageFieldFile.delete()`` and
        ``FieldFile.delete()`` but with the attempts to reset the instance
        property removed.

        """
        # Clear the image dimensions cache
        if hasattr(self, '_dimensions_cache'):
            del self._dimensions_cache

        # Only close the file if it's already open, which we know by the
        # presence of self._file.
        if hasattr(self, '_file'):
            self.close()
            del self.file

        if self.name and self.storage.exists(self.name):
            try:
                self.storage.delete(self.name)
            except NotImplementedError:
                pass

        # Delete the filesize cache.
        if hasattr(self, '_size'):
            del self._size
        self._committed = False

        if save:
            self.instance.save()

    @property
    def name(self):
        """
        Specifies the filename that the cached image will use.

        """
        return self.field.generator.generate_filename(self.source_file)

    @name.setter
    def name(self, value):
        # TODO: Figure out a better way to handle this. We really don't want
        # to allow anybody to set the name, but ``File.__init__`` (which is
        # called by ``ImageSpecFieldFile.__init__``) does, so we have to allow
        # it at least that one time.
        pass

    @property
    def storage(self):
        return getattr(self, '_storage', None) or self.field.storage or self.source_file.storage

    @storage.setter
    def storage(self, storage):
        self._storage = storage

    def __getstate__(self):
        return dict(
            attname=self.attname,
            instance=self.instance,
        )

    def __setstate__(self, state):
        self.attname = state['attname']
        self.instance = state['instance']
        self.field = getattr(self.instance.__class__, self.attname)


class ProcessedImageFieldFile(ImageFieldFile):
    def save(self, name, content, save=True):
        new_filename = self.field.generate_filename(self.instance, name)
        img, content = self.field.generator.process_content(content,
                new_filename, self)
        return super(ProcessedImageFieldFile, self).save(name, content, save)
