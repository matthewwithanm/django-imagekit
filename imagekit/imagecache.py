from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module


class PessimisticImageCacheBackend(object):
    """
    A very safe image cache backend. Guarantees that files will always be
    available, but at the cost of hitting the storage backend.

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


class NonValidatingImageCacheBackend(object):
    """
    A backend that is super optimistic about the existence of spec files. It
    will hit your file storage much less frequently than the pessimistic
    backend, but it is technically possible for a cache file to be missing
    after validation.

    """

    def validate(self, file):
        """
        NonValidatingImageCacheBackend has faith, so validate's a no-op.

        """
        pass

    def invalidate(self, file):
        """
        Immediately generate a new spec file upon invalidation.

        """
        file.generate(save=True)

    def clear(self, file):
        file.delete(save=False)


_default_image_cache_backend = None


def get_default_image_cache_backend():
    """
    Get the default image cache backend. Uses the same method as
    django.core.file.storage.get_storage_class

    """
    global _default_image_cache_backend
    if not _default_image_cache_backend:
        from .settings import DEFAULT_IMAGE_CACHE_BACKEND as import_path
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
