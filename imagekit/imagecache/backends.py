from ..utils import get_singleton
from django.core.cache import get_cache
from django.core.cache.backends.dummy import DummyCache
from django.core.exceptions import ImproperlyConfigured


def get_default_image_cache_backend():
    """
    Get the default image cache backend.

    """
    from django.conf import settings
    return get_singleton(settings.IMAGEKIT_DEFAULT_IMAGE_CACHE_BACKEND,
            'image cache backend')


class InvalidImageCacheBackendError(ImproperlyConfigured):
    pass


class CachedValidationBackend(object):
    @property
    def cache(self):
        if not getattr(self, '_cache', None):
            from django.conf import settings
            alias = settings.IMAGEKIT_CACHE_BACKEND
            self._cache = get_cache(alias) if alias else DummyCache(None, {})
        return self._cache

    def get_key(self, file):
        from django.conf import settings
        return '%s%s-valid' % (settings.IMAGEKIT_CACHE_PREFIX, file.get_hash())

    def is_invalid(self, file):
        key = self.get_key(file)
        cached_value = self.cache.get(key)
        if cached_value is None:
            cached_value = self._is_invalid(file)
            self.cache.set(key, cached_value)
        return cached_value

    def validate(self, file):
        if self.is_invalid(file):
            self._validate(file)
            self.cache.set(self.get_key(file), True)

    def invalidate(self, file):
        if not self.is_invalid(file):
            self._invalidate(file)
            self.cache.set(self.get_key(file), False)


class Simple(CachedValidationBackend):
    """
    The most basic image cache backend. Files are considered valid if they
    exist. To invalidate a file, it's deleted; to validate one, it's generated
    immediately.

    """

    def _is_invalid(self, file):
        if not getattr(file, '_file', None):
            # No file on object. Have to check storage.
            return not file.storage.exists(file.name)
        return False

    def _validate(self, file):
        """
        Generates a new image by running the processors on the source file.

        """
        file.generate(save=True)

    def invalidate(self, file):
        """
        Invalidate the file by deleting it. We override ``invalidate()``
        instead of ``_invalidate()`` because we don't really care to check
        whether the file is invalid or not.

        """
        file.delete(save=False)

    def clear(self, file):
        file.delete(save=False)
