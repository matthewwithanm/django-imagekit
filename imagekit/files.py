from django.conf import settings
from django.core.files.base import ContentFile, File
from django.core.files.images import ImageFile
from django.utils.encoding import smart_str, smart_unicode
import os
from .signals import before_access
from .utils import (suggest_extension, format_to_mimetype,
                    extension_to_mimetype)


class BaseIKFile(File):
    """
    This class contains all of the methods we need from
    django.db.models.fields.files.FieldFile, but with the model stuff ripped
    out. It's only extended by one class, but we keep it separate for
    organizational reasons.

    """

    def __init__(self):
        pass

    def _require_file(self):
        if not self:
            raise ValueError()

    def _get_file(self):
        self._require_file()
        if not hasattr(self, '_file') or self._file is None:
            self._file = self.storage.open(self.name, 'rb')
        return self._file

    def _set_file(self, file):
        self._file = file

    def _del_file(self):
        del self._file

    file = property(_get_file, _set_file, _del_file)

    def _get_path(self):
        self._require_file()
        return self.storage.path(self.name)
    path = property(_get_path)

    def _get_url(self):
        self._require_file()
        return self.storage.url(self.name)
    url = property(_get_url)

    def _get_size(self):
        self._require_file()
        if not self._committed:
            return self.file.size
        return self.storage.size(self.name)
    size = property(_get_size)

    def open(self, mode='rb'):
        self._require_file()
        self.file.open(mode)

    def _get_closed(self):
        file = getattr(self, '_file', None)
        return file is None or file.closed
    closed = property(_get_closed)

    def close(self):
        file = getattr(self, '_file', None)
        if file is not None:
            file.close()


class ImageSpecCacheFile(ImageFile, BaseIKFile):
    def __init__(self, spec, source_file):
        self.storage = spec.storage or source_file.storage
        self.spec = spec
        self.source_file = source_file

    def get_hash(self):
        return self.spec.get_hash(self.source_file)

    def _require_file(self):
        before_access.send(sender=self, spec=self.spec, file=self)
        return super(ImageSpecCacheFile, self)._require_file()

    @property
    def name(self):
        source_filename = self.source_file.name
        filename = None
        if source_filename:
            hash = self.spec.get_hash(self.source_file)
            ext = suggest_extension(source_filename, self.spec.format)
            filename = os.path.normpath(os.path.join(
                    settings.IMAGEKIT_CACHE_DIR,
                    os.path.splitext(source_filename)[0],
                    '%s%s' % (hash, ext)))

        return filename

    def clear(self):
        return self.spec.image_cache_backend.clear(self)

    def invalidate(self):
        return self.spec.image_cache_backend.invalidate(self)

    def validate(self):
        return self.spec.image_cache_backend.validate(self)

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
