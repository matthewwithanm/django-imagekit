from imagekit.utils import get_spec_files
from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module


class DefaultCacheStateBackend(object):

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
            content = file.generate()
            if content:
                file.storage.save(file.name, content)

    def invalidate(self, file):
        file.delete(save=False)


_default_cache_state_backend = None


def get_default_cache_state_backend():
    """
    Get the default cache state backend. Uses the same method as
    django.core.file.storage.get_storage_class

    """
    global _default_cache_state_backend
    if not _default_cache_state_backend:
        from ..settings import DEFAULT_CACHE_STATE_BACKEND as import_path
        try:
            dot = import_path.rindex('.')
        except ValueError:
            raise ImproperlyConfigured("%s isn't a cache state backend module." % \
                    import_path)
        module, classname = import_path[:dot], import_path[dot+1:]
        try:
            mod = import_module(module)
        except ImportError, e:
            raise ImproperlyConfigured('Error importing cache state module %s: "%s"' % (module, e))
        try:
            cls = getattr(mod, classname)
            _default_cache_state_backend = cls()
        except AttributeError:
            raise ImproperlyConfigured('Cache state backend module "%s" does not define a "%s" class.' % (module, classname))
    return _default_cache_state_backend
