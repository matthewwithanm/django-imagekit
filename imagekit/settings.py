from django.conf import settings

DEFAULT_IMAGE_CACHE_BACKEND = getattr(settings,
        'IMAGEKIT_DEFAULT_IMAGE_CACHE_BACKEND',
        'imagekit.imagecache.PessimisticImageCacheBackend')
