from appconf import AppConf
from django.conf import settings


class ImageKitConf(AppConf):
    CACHEFILE_NAMER = 'imagekit.cachefiles.namers.hash'
    SPEC_CACHEFILE_NAMER = 'imagekit.cachefiles.namers.source_name_as_path'
    CACHEFILE_DIR = 'CACHE/images'
    DEFAULT_CACHEFILE_BACKEND = 'imagekit.cachefiles.backends.Simple'
    DEFAULT_CACHEFILE_STRATEGY = 'imagekit.cachefiles.strategies.JustInTime'

    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

    CACHE_BACKEND = None
    CACHE_PREFIX = 'imagekit:'

    def configure_cache_backend(self, value):
        if value is None:
            if getattr(settings, 'CACHES', None):
                value = 'django.core.cache.backends.dummy.DummyCache' if settings.DEBUG else 'default'
            else:
                value = 'dummy://' if settings.DEBUG else settings.CACHE_BACKEND
        return value
