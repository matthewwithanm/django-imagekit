from appconf import AppConf
from django.conf import settings


class ImageKitConf(AppConf):
    CACHEFILE_NAMER = 'imagekit.cachefiles.namers.hash'
    SPEC_CACHEFILE_NAMER = 'imagekit.cachefiles.namers.source_name_as_path'
    CACHEFILE_DIR = 'CACHE/images'
    DEFAULT_CACHEFILE_BACKEND = 'imagekit.cachefiles.backends.Simple'
    DEFAULT_CACHEFILE_STRATEGY = 'imagekit.cachefiles.strategies.JustInTime'

    DEFAULT_FILE_STORAGE = None

    CACHE_BACKEND = None
    CACHE_PREFIX = 'imagekit:'
    USE_MEMCACHED_SAFE_CACHE_KEY = True

    def configure_cache_backend(self, value):
        if value is None:
            # DummyCache doesn't exist in Django<=1.2
            try:
                from django.core.cache.backends.dummy import DummyCache
            except ImportError:
                dummy_cache = 'dummy://'
            else:
                dummy_cache = '{0.__module__}.{0.__name__}'.format(DummyCache)

            # DEFAULT_CACHE_ALIAS doesn't exist in Django<=1.2
            try:
                from django.core.cache import DEFAULT_CACHE_ALIAS
                default_cache_alias = DEFAULT_CACHE_ALIAS
            except ImportError:
                default_cache_alias = 'default'

            if settings.DEBUG:
                value = dummy_cache
            else:
                newstyle_cache = getattr(settings, 'CACHES', {}) \
                                   .get(default_cache_alias, {}).get('BACKEND')
                oldstyle_cache = getattr(settings, 'CACHE_BACKEND', None)
                value = newstyle_cache or oldstyle_cache or dummy_cache

        return value

    def configure_default_file_storage(self, value):
        if value is None:
            value = settings.DEFAULT_FILE_STORAGE
        return value
