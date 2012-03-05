from django.core.exceptions import ImproperlyConfigured


class InvalidImageCacheBackendError(ImproperlyConfigured):
    pass


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
