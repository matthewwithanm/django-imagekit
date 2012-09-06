from appconf import AppConf


class ImageKitConf(AppConf):
    DEFAULT_IMAGE_CACHE_BACKEND = 'imagekit.imagecache.backends.Simple'
    CACHE_BACKEND = None
    VALIDATE_ON_ACCESS = True
    CACHE_DIR = 'CACHE/images'
    CACHE_PREFIX = 'ik-'
