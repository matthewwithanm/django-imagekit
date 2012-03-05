from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module

from imagekit.imagecache.base import InvalidImageCacheBackendError, PessimisticImageCacheBackend, NonValidatingImageCacheBackend

_default_image_cache_backend = None


def get_default_image_cache_backend():
    """
    Get the default image cache backend. Uses the same method as
    django.core.file.storage.get_storage_class

    """
    global _default_image_cache_backend
    if not _default_image_cache_backend:
        from ..settings import DEFAULT_IMAGE_CACHE_BACKEND as import_path
        try:
            dot = import_path.rindex('.')
        except ValueError:
            raise ImproperlyConfigured("%s isn't an image cache backend module." % \
                    import_path)
        module, classname = import_path[:dot], import_path[dot + 1:]
        try:
            mod = import_module(module)
        except ImportError, e:
            raise ImproperlyConfigured('Error importing image cache backend module %s: "%s"' % (module, e))
        try:
            cls = getattr(mod, classname)
            _default_image_cache_backend = cls()
        except AttributeError:
            raise ImproperlyConfigured('Image cache backend module "%s" does not define a "%s" class.' % (module, classname))
    return _default_image_cache_backend
