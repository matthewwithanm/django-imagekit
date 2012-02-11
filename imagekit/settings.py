from django.conf import settings

DEFAULT_CACHE_STATE_BACKEND = getattr(settings,
        'IMAGEKIT_DEFAULT_CACHE_STATE_BACKEND',
        'imagekit.cachestate.PessimisticCacheStateBackend')
