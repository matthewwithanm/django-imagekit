import os
import datetime

from django.db.models.fields.files import ImageField, ImageFieldFile
from django.utils.encoding import force_unicode, smart_str


class ImageSpecFieldFile(ImageFieldFile):
    def __init__(self, instance, field, attname):
        super(ImageSpecFieldFile, self).__init__(instance, field, None)
        self.attname = attname
        self.storage = self.field.storage or self.source_file.storage

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
        else:
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

    def _default_cache_to(self, instance, path, specname, extension):
        """
        Determines the filename to use for the transformed image. Can be
        overridden on a per-spec basis by setting the cache_to property on
        the spec.

        """
        filepath, basename = os.path.split(path)
        filename = os.path.splitext(basename)[0]
        new_name = '%s_%s%s' % (filename, specname, extension)
        return os.path.join(os.path.join('cache', filepath), new_name)

    @property
    def name(self):
        """
        Specifies the filename that the cached image will use. The user can
        control this by providing a `cache_to` method to the ImageSpecField.

        """
        name = getattr(self, '_name', None)
        if not name:
            filename = self.source_file.name
            new_filename = None
            if filename:
                cache_to = self.field.cache_to or self._default_cache_to

                if not cache_to:
                    raise Exception('No cache_to or default_cache_to value'
                            ' specified')
                if callable(cache_to):
                    suggested_extension = \
                            self.field.generator.suggest_extension(
                            self.source_file.name)
                    new_filename = force_unicode(
                            datetime.datetime.now().strftime(
                            smart_str(cache_to(self.instance,
                            self.source_file.name, self.attname,
                            suggested_extension))))
                else:
                    dir_name = os.path.normpath(
                            force_unicode(datetime.datetime.now().strftime(
                            smart_str(cache_to))))
                    filename = os.path.normpath(os.path.basename(filename))
                    new_filename = os.path.join(dir_name, filename)

            self._name = new_filename
        return self._name

    @name.setter
    def name(self, value):
        # TODO: Figure out a better way to handle this. We really don't want
        # to allow anybody to set the name, but ``File.__init__`` (which is
        # called by ``ImageSpecFieldFile.__init__``) does, so we have to allow
        # it at least that one time.
        pass


class ProcessedImageFieldFile(ImageFieldFile):
    def save(self, name, content, save=True):
        new_filename = self.field.generate_filename(self.instance, name)
        img, content = self.field.generator.process_content(content,
                new_filename, self)
        return super(ProcessedImageFieldFile, self).save(name, content, save)
