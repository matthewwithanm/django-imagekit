from appconf import AppConf
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class ImageKitConf(AppConf):
    CACHEFILE_NAMER = 'imagekit.cachefiles.namers.hash'
    SPEC_CACHEFILE_NAMER = 'imagekit.cachefiles.namers.source_name_as_path'
    CACHEFILE_DIR = 'CACHE/images'
    DEFAULT_CACHEFILE_BACKEND = 'imagekit.cachefiles.backends.Simple'
    DEFAULT_CACHEFILE_STRATEGY = 'imagekit.cachefiles.strategies.JustInTime'

    DEFAULT_FILE_STORAGE = None

    CACHE_BACKEND = None
    CACHE_PREFIX = 'imagekit:'
    CACHE_TIMEOUT = None
    USE_MEMCACHED_SAFE_CACHE_KEY = True

    def configure_cache_backend(self, value):
        if value is None:
            from django.core.cache import DEFAULT_CACHE_ALIAS
            return DEFAULT_CACHE_ALIAS

        if value not in settings.CACHES:
            raise ImproperlyConfigured("{0} is not present in settings.CACHES".format(value))

        return value

    def configure_cache_timeout(self, value):
        if value is None and settings.DEBUG:
            # If value is not configured and is DEBUG set it to 5 minutes
            return 300
        # Otherwise leave it as is. If it is None then valies will never expire
        return value

    def configure_default_file_storage(self, value):
        if value is None:
            value = settings.DEFAULT_FILE_STORAGE
        return value
