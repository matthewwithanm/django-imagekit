from django.core.files.base import ContentFile
from django.db.models.fields.files import ImageFieldFile
from django.utils.encoding import smart_str, smart_unicode
import os
from .utils import (SpecWrapper, suggest_extension, format_to_mimetype,
                    extension_to_mimetype)


class ImageSpecFile(ImageFieldFile):
    def __init__(self, spec, source_file, spec_id):
        spec = SpecWrapper(spec)

        self.storage = spec.storage or source_file.storage

        self.spec = spec
        self.source_file = source_file
        self.spec_id = spec_id

    def get_hash(self):
        return self.spec.get_hash(self.source_file)

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
        name = self.spec.generate_filename(self.source_file)
        if name is not None:
            return name
        else:
            source_filename = self.source_file.name
            filepath, basename = os.path.split(source_filename)
            filename = os.path.splitext(basename)[0]
            extension = suggest_extension(source_filename, self.spec.format)
            new_name = '%s%s' % (filename, extension)
            cache_filename = ['cache', 'iktt'] + self.spec_id.split(':') + \
                    [filepath, new_name]
            return os.path.join(*cache_filename)

    def generate(self, save=True):
        return self.spec.generate_file(self.name, self.source_file, save)


class IKContentFile(ContentFile):
    """
    Wraps a ContentFile in a file-like object with a filename and a
    content_type. A PIL image format can be optionally be provided as a content
    type hint.

    """
    def __init__(self, filename, content, format=None):
        self.file = ContentFile(content)
        self.file.name = filename
        mimetype = getattr(self.file, 'content_type', None)
        if format and not mimetype:
            mimetype = format_to_mimetype(format)
        if not mimetype:
            ext = os.path.splitext(filename or '')[1]
            mimetype = extension_to_mimetype(ext)
        self.file.content_type = mimetype

    def __str__(self):
        return smart_str(self.file.name or '')

    def __unicode__(self):
        return smart_unicode(self.file.name or u'')
