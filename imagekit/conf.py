from appconf import AppConf
from .imagecache.actions import validate_now, clear_now


class ImageKitConf(AppConf):
    DEFAULT_IMAGE_CACHE_BACKEND = 'imagekit.imagecache.backends.Simple'
    CACHE_BACKEND = None
    CACHE_DIR = 'CACHE/images'
    CACHE_PREFIX = 'ik-'
    DEFAULT_SPEC_FIELD_IMAGE_CACHE_STRATEGY = 'imagekit.imagecache.strategies.Pessimistic'
