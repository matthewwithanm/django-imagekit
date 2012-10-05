from appconf import AppConf
from django.conf import settings


class ImageKitConf(AppConf):
    DEFAULT_IMAGE_CACHE_BACKEND = 'imagekit.imagecache.backends.Simple'
    CACHE_BACKEND = None
    CACHE_DIR = 'CACHE/images'
    CACHE_PREFIX = 'ik-'
    DEFAULT_IMAGE_CACHE_STRATEGY = 'imagekit.imagecache.strategies.Pessimistic'

    def configure_cache_backend(self, value):
        if value is None:
            value = 'django.core.cache.backends.dummy.DummyCache' if settings.DEBUG else 'default'
        return value
