from django.conf import settings
from django.core.files.base import ContentFile, File
from django.core.files.images import ImageFile
from django.utils.encoding import smart_str, smart_unicode
from django.utils.functional import LazyObject
import os
from .registry import generator_registry
from .signals import before_access
from .utils import (format_to_mimetype, extension_to_mimetype, get_logger,
    get_singleton, generate)


class BaseIKFile(File):
    """
    This class contains all of the methods we need from
    django.db.models.fields.files.FieldFile, but with the model stuff ripped
    out. It's only extended by one class, but we keep it separate for
    organizational reasons.

    """

    def __init__(self, storage):
        self.storage = storage

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


class GeneratedImageCacheFile(BaseIKFile, ImageFile):
    """
    A cache file that represents the result of a generator. Creating an instance
    of this class is not enough to trigger the creation of the cache file. In
    fact, one of the main points of this class is to allow the creation of the
    file to be deferred until the time that the image cache strategy requires
    it.

    """
    def __init__(self, generator, name=None, storage=None, image_cache_backend=None):
        """
        :param generator: The object responsible for generating a new image.
        :param name: The filename
        :param storage: A Django storage object that will be used to save the
            file.
        :param image_cache_backend: The object responsible for managing the
            state of the cache file.

        """
        self.generator = generator

        self.name = name or getattr(generator, 'cache_file_name', None)
        storage = storage or getattr(generator, 'cache_file_storage',
            None) or get_singleton(settings.IMAGEKIT_DEFAULT_FILE_STORAGE,
            'file storage backend')
        self.image_cache_backend = image_cache_backend or getattr(generator,
            'image_cache_backend', None)

        super(GeneratedImageCacheFile, self).__init__(storage=storage)

    def _require_file(self):
        before_access.send(sender=self, generator=self.generator, file=self)
        return super(GeneratedImageCacheFile, self)._require_file()

    def clear(self):
        return self.image_cache_backend.clear(self)

    def invalidate(self):
        return self.image_cache_backend.invalidate(self)

    def validate(self):
        return self.image_cache_backend.validate(self)

    def generate(self):
        # Generate the file
        content = generate(self.generator)

        actual_name = self.storage.save(self.name, content)

        if actual_name != self.name:
            get_logger().warning('The storage backend %s did not save the file'
                    ' with the requested name ("%s") and instead used'
                    ' "%s". This may be because a file already existed with'
                    ' the requested name. If so, you may have meant to call'
                    ' validate() instead of generate(), or there may be a'
                    ' race condition in the image cache backend %s. The'
                    ' saved file will not be used.' % (self.storage,
                    self.name, actual_name,
                    self.image_cache_backend))


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

    @property
    def name(self):
        return self.file.name

    def __str__(self):
        return smart_str(self.file.name or '')

    def __unicode__(self):
        return smart_unicode(self.file.name or u'')


class LazyGeneratedImageCacheFile(LazyObject):
    def __init__(self, generator_id, *args, **kwargs):
        super(LazyGeneratedImageCacheFile, self).__init__()

        def setup():
            generator = generator_registry.get(generator_id, *args, **kwargs)
            self._wrapped = GeneratedImageCacheFile(generator)

        self.__dict__['_setup'] = setup
