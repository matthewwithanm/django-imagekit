from appconf import AppConf
from django.conf import settings


class ImageKitConf(AppConf):
    GENERATEDFILE_NAMER = 'imagekit.generatedfiles.namers.hash'
    SPEC_GENERATEDFILE_NAMER = 'imagekit.generatedfiles.namers.source_name_as_path'
    GENERATEDFILE_DIR = 'generated/images'
    DEFAULT_GENERATEDFILE_BACKEND = 'imagekit.generatedfiles.backends.Simple'
    DEFAULT_GENERATEDFILE_STRATEGY = 'imagekit.generatedfiles.strategies.JustInTime'

    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

    CACHE_BACKEND = None
    CACHE_PREFIX = 'imagekit:'

    def configure_cache_backend(self, value):
        if value is None:
            value = 'django.core.cache.backends.dummy.DummyCache' if settings.DEBUG else 'default'
        return value
