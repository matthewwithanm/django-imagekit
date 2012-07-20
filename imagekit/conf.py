from appconf import AppConf


class ImageKitConf(AppConf):
    DEFAULT_IMAGE_CACHE_BACKEND = 'imagekit.imagecache.PessimisticImageCacheBackend'
