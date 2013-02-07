from ..utils import get_singleton
from django.core.cache import get_cache
from django.core.exceptions import ImproperlyConfigured


def get_default_cachefile_backend():
    """
    Get the default file backend.

    """
    from django.conf import settings
    return get_singleton(settings.IMAGEKIT_DEFAULT_CACHEFILE_BACKEND,
            'file backend')


class InvalidFileBackendError(ImproperlyConfigured):
    pass


class CachedFileBackend(object):
    @property
    def cache(self):
        if not getattr(self, '_cache', None):
            from django.conf import settings
            self._cache = get_cache(settings.IMAGEKIT_CACHE_BACKEND)
        return self._cache

    def get_key(self, file):
        from django.conf import settings
        return '%s%s-exists' % (settings.IMAGEKIT_CACHE_PREFIX, file.name)

    def file_exists(self, file):
        key = self.get_key(file)
        exists = self.cache.get(key)
        if exists is None:
            exists = self._file_exists(file)
            self.cache.set(key, exists)
        return exists

    def ensure_exists(self, file):
        if self.file_exists(file):
            self.create(file)
            self.cache.set(self.get_key(file), True)


class Simple(CachedFileBackend):
    """
    The most basic file backend. The storage is consulted to see if the file
    exists.

    """

    def _file_exists(self, file):
        if not getattr(file, '_file', None):
            # No file on object. Have to check storage.
            return not file.storage.exists(file.name)
        return False

    def create(self, file):
        """
        Generates a new image by running the processors on the source file.

        """
        file.generate(force=True)
