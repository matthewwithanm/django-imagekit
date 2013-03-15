from ..utils import get_singleton
from django.core.cache import get_cache
from django.core.exceptions import ImproperlyConfigured


class CacheFileState(object):
    EXISTS = 'exists'
    PENDING = 'pending'
    DOES_NOT_EXIST = 'does_not_exist'


def get_default_cachefile_backend():
    """
    Get the default file backend.

    """
    from django.conf import settings
    return get_singleton(settings.IMAGEKIT_DEFAULT_CACHEFILE_BACKEND,
            'file backend')


class InvalidFileBackendError(ImproperlyConfigured):
    pass


class AbstractCacheFileBackend(object):
    """
    An abstract cache file backend. This isn't used by any internal classes and
    is included simply to illustrate the minimum interface of a cache file
    backend for users who wish to implement their own.

    """
    def generate(self, file, force=False):
        raise NotImplementedError

    def exists(self, file):
        raise NotImplementedError


class CachedFileBackend(object):
    @property
    def cache(self):
        if not getattr(self, '_cache', None):
            from django.conf import settings
            self._cache = get_cache(settings.IMAGEKIT_CACHE_BACKEND)
        return self._cache

    def get_key(self, file):
        from django.conf import settings
        return '%s%s-state' % (settings.IMAGEKIT_CACHE_PREFIX, file.name)

    def get_state(self, file):
        key = self.get_key(file)
        state = self.cache.get(key)
        if state is None:
            exists = self._exists(file)
            state = CacheFileState.EXISTS if exists else CacheFileState.DOES_NOT_EXIST
            self.set_state(file, state)
        return state

    def set_state(self, file, state):
        key = self.get_key(file)
        self.cache.set(key, state)

    def exists(self, file):
        return self.get_state(file) is CacheFileState.EXISTS

    def generate(self, file, force=False):
        if force:
            file._generate()
            self.set_state(file, CacheFileState.EXISTS)
        elif self.get_state(file) is CacheFileState.DOES_NOT_EXIST:
            # Don't generate if the file exists or is pending.
            self._generate(file)


class Simple(CachedFileBackend):
    """
    The most basic file backend. The storage is consulted to see if the file
    exists. Files are generated synchronously.

    """

    def _generate(self, file):
        file._generate()
        self.set_state(file, CacheFileState.EXISTS)

    def _exists(self, file):
        return bool(getattr(file, '_file', None)
                    or file.storage.exists(file.name))
