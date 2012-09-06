from ..utils import get_singleton
from .base import InvalidImageCacheBackendError, PessimisticImageCacheBackend


def get_default_image_cache_backend():
    """
    Get the default validation backend.

    """
    from django.conf import settings
    return get_singleton(settings.IMAGEKIT_DEFAULT_IMAGE_CACHE_BACKEND,
            'image cache backend')
