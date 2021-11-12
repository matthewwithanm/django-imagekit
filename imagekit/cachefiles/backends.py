import warnings
from copy import copy

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from ..utils import get_cache, get_singleton, sanitize_cache_key


class CacheFileState:
    EXISTS = 'exists'
    GENERATING = 'generating'
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


class AbstractCacheFileBackend:
    """
    An abstract cache file backend. This isn't used by any internal classes and
    is included simply to illustrate the minimum interface of a cache file
    backend for users who wish to implement their own.

    """
    def generate(self, file, force=False):
        raise NotImplementedError

    def exists(self, file):
        raise NotImplementedError


class CachedFileBackend:
    existence_check_timeout = 5
    """
    The number of seconds to wait before rechecking to see if the file exists.
    If the image is found to exist, that information will be cached using the
    timeout specified in your CACHES setting (which should be very high).
    However, when the file does not exist, you probably want to check again
    in a relatively short amount of time. This attribute allows you to do that.

    """

    @property
    def cache(self):
        if not getattr(self, '_cache', None):
            self._cache = get_cache()
        return self._cache

    def get_key(self, file):
        from django.conf import settings
        return sanitize_cache_key('%s%s-state' %
                                  (settings.IMAGEKIT_CACHE_PREFIX, file.name))

    def get_state(self, file, check_if_unknown=True):
        key = self.get_key(file)
        state = self.cache.get(key)
        if state is None and check_if_unknown:
            exists = self._exists(file)
            state = CacheFileState.EXISTS if exists else CacheFileState.DOES_NOT_EXIST
            self.set_state(file, state)
        return state

    def set_state(self, file, state):
        key = self.get_key(file)
        if state == CacheFileState.DOES_NOT_EXIST:
            self.cache.set(key, state, self.existence_check_timeout)
        else:
            self.cache.set(key, state, settings.IMAGEKIT_CACHE_TIMEOUT)

    def __getstate__(self):
        state = copy(self.__dict__)
        # Don't include the cache when pickling. It'll be reconstituted based
        # on the settings.
        state.pop('_cache', None)
        return state

    def exists(self, file):
        return self.get_state(file) == CacheFileState.EXISTS

    def generate(self, file, force=False):
        raise NotImplementedError

    def generate_now(self, file, force=False):
        if force or self.get_state(file) not in (CacheFileState.GENERATING, CacheFileState.EXISTS):
            self.set_state(file, CacheFileState.GENERATING)
            file._generate()
            self.set_state(file, CacheFileState.EXISTS)
            file.close()


class Simple(CachedFileBackend):
    """
    The most basic file backend. The storage is consulted to see if the file
    exists. Files are generated synchronously.

    """

    def generate(self, file, force=False):
        self.generate_now(file, force=force)

    def _exists(self, file):
        return bool(getattr(file, '_file', None)
                    or (file.name and file.storage.exists(file.name)))


def _generate_file(backend, file, force=False):
    backend.generate_now(file, force=force)


class BaseAsync(Simple):
    """
    Base class for cache file backends that generate files asynchronously.
    """
    is_async = True

    def generate(self, file, force=False):
        # Schedule the file for generation, unless we know for sure we don't
        # need to. If an already-generated file sneaks through, that's okay;
        # ``generate_now`` will catch it. We just want to make sure we don't
        # schedule anything we know is unnecessary--but we also don't want to
        # force a costly existence check.
        state = self.get_state(file, check_if_unknown=False)
        if state not in (CacheFileState.GENERATING, CacheFileState.EXISTS):
            self.schedule_generation(file, force=force)

    def schedule_generation(self, file, force=False):
        # overwrite this to have the file generated in the background,
        # e. g. in a worker queue.
        raise NotImplementedError


try:
    from celery import shared_task as task
except ImportError:
    pass
else:
    _celery_task = task(ignore_result=True, serializer='pickle')(_generate_file)


class Celery(BaseAsync):
    """
    A backend that uses Celery to generate the images.
    """
    def __init__(self, *args, **kwargs):
        try:
            import celery  # noqa
        except ImportError:
            raise ImproperlyConfigured('You must install celery to use'
                                       ' imagekit.cachefiles.backends.Celery.')
        super().__init__(*args, **kwargs)

    def schedule_generation(self, file, force=False):
        _celery_task.delay(self, file, force=force)


# Stub class to preserve backwards compatibility and issue a warning
class Async(Celery):
    def __init__(self, *args, **kwargs):
        message = '{path}.Async is deprecated. Use {path}.Celery instead.'
        warnings.warn(message.format(path=__name__), DeprecationWarning)
        super().__init__(*args, **kwargs)


try:
    from django_rq import job
except ImportError:
    pass
else:
    _rq_job = job('default', result_ttl=0)(_generate_file)


class RQ(BaseAsync):
    """
    A backend that uses RQ to generate the images.
    """
    def __init__(self, *args, **kwargs):
        try:
            import django_rq  # noqa
        except ImportError:
            raise ImproperlyConfigured('You must install django-rq to use'
                                       ' imagekit.cachefiles.backends.RQ.')
        super().__init__(*args, **kwargs)

    def schedule_generation(self, file, force=False):
        _rq_job.delay(self, file, force=force)


try:
    from dramatiq import actor
except ImportError:
    pass
else:
    _dramatiq_actor = actor()(_generate_file)


class Dramatiq(BaseAsync):
    """
    A backend that uses Dramatiq to generate the images.
    """
    def __init__(self, *args, **kwargs):
        try:
            import dramatiq  # noqa
        except ImportError:
            raise ImproperlyConfigured('You must install django-dramatiq to use'
                                        ' imagekit.cachefiles.backends.Dramatiq.')
        super().__init__(*args, **kwargs)

    def schedule_generation(self, file, force=False):
        _dramatiq_actor.send(self, file, force=force)
