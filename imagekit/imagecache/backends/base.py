from ...utils import get_singleton
from django.core.exceptions import ImproperlyConfigured


def get_default_image_cache_backend():
    """
    Get the default image cache backend.

    """
    from django.conf import settings
    return get_singleton(settings.IMAGEKIT_DEFAULT_IMAGE_CACHE_BACKEND,
            'image cache backend')


class InvalidImageCacheBackendError(ImproperlyConfigured):
    pass


class Simple(object):
    """
    The most basic image cache backend. Files are considered valid if they
    exist. To invalidate a file, it's deleted; to validate one, it's generated
    immediately.

    """

    def is_invalid(self, file):
        if not getattr(file, '_file', None):
            # No file on object. Have to check storage.
            return not file.storage.exists(file.name)
        return False

    def validate(self, file):
        """
        Generates a new image by running the processors on the source file.

        """
        if self.is_invalid(file):
            file.generate(save=True)

    def invalidate(self, file):
        file.delete(save=False)

    def clear(self, file):
        file.delete(save=False)
