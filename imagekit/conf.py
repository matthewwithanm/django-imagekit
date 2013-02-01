from appconf import AppConf
from django.conf import settings


class ImageKitConf(AppConf):
    DEFAULT_GENERATEDFILE_BACKEND = 'imagekit.generatedfiles.backends.Simple'
    CACHE_BACKEND = None
    GENERATED_FILE_DIR = 'generated/images'
    CACHE_PREFIX = 'imagekit:'
    DEFAULT_GENERATEDFILE_STRATEGY = 'imagekit.generatedfiles.strategies.JustInTime'
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

    def configure_cache_backend(self, value):
        if value is None:
            value = 'django.core.cache.backends.dummy.DummyCache' if settings.DEBUG else 'default'
        return value
