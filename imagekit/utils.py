from __future__ import unicode_literals
import logging
import re
from tempfile import NamedTemporaryFile
from hashlib import md5

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files import File
try:
    from importlib import import_module
except ImportError:
    from django.utils.importlib import import_module
from pilkit.utils import *
from .lib import NullHandler, force_bytes


bad_memcached_key_chars = re.compile('[\u0000-\u001f\\s]+')

_autodiscovered = False

def get_nonabstract_descendants(model):
    """ Returns all non-abstract descendants of the model. """
    if not model._meta.abstract:
        yield model
    for s in model.__subclasses__():
        for m in get_nonabstract_descendants(s):
            yield m


def get_by_qname(path, desc):
    try:
        dot = path.rindex('.')
    except ValueError:
        raise ImproperlyConfigured("%s isn't a %s module." % (path, desc))
    module, objname = path[:dot], path[dot + 1:]
    try:
        mod = import_module(module)
    except ImportError as e:
        raise ImproperlyConfigured('Error importing %s module %s: "%s"' %
                (desc, module, e))
    try:
        obj = getattr(mod, objname)
        return obj
    except AttributeError:
        raise ImproperlyConfigured('%s module "%s" does not define "%s"'
                % (desc[0].upper() + desc[1:], module, objname))


_singletons = {}


def get_singleton(class_path, desc):
    global _singletons
    cls = get_by_qname(class_path, desc)
    instance = _singletons.get(cls)
    if not instance:
        instance = _singletons[cls] = cls()
    return instance


def autodiscover():
    """
    Auto-discover INSTALLED_APPS imagegenerators.py modules and fail silently
    when not present. This forces an import on them to register any admin bits
    they may want.

    Copied from django.contrib.admin
    """
    global _autodiscovered

    if _autodiscovered:
        return

    try:
        from django.utils.module_loading import autodiscover_modules
    except ImportError:
        # Django<1.7
        _autodiscover_modules_fallback()
    else:
        autodiscover_modules('imagegenerators')
    _autodiscovered = True


def _autodiscover_modules_fallback():
    """
    Auto-discover INSTALLED_APPS imagegenerators.py modules and fail silently
    when not present. This forces an import on them to register any admin bits
    they may want.

    Copied from django.contrib.admin

    Used for Django versions < 1.7
    """
    from django.conf import settings
    try:
        from importlib import import_module
    except ImportError:
        from django.utils.importlib import import_module
    from django.utils.module_loading import module_has_submodule

    for app in settings.INSTALLED_APPS:
        # As of Django 1.7, settings.INSTALLED_APPS may contain classes instead of modules, hence the try/except
        # See here: https://docs.djangoproject.com/en/dev/releases/1.7/#introspecting-applications
        try:
            mod = import_module(app)
            # Attempt to import the app's admin module.
            try:
                import_module('%s.imagegenerators' % app)
            except:
                # Decide whether to bubble up this error. If the app just
                # doesn't have an imagegenerators module, we can ignore the error
                # attempting to import it, otherwise we want it to bubble up.
                if module_has_submodule(mod, 'imagegenerators'):
                    raise
        except ImportError:
            pass


def get_logger(logger_name='imagekit', add_null_handler=True):
    logger = logging.getLogger(logger_name)
    if add_null_handler:
        logger.addHandler(NullHandler())
    return logger


def get_field_info(field_file):
    """
    A utility for easily extracting information about the host model from a
    Django FileField (or subclass). This is especially useful for when you want
    to alter processors based on a property of the source model. For example::

        class MySpec(ImageSpec):
            def __init__(self, source):
                instance, attname = get_field_info(source)
                self.processors = [SmartResize(instance.thumbnail_width,
                                               instance.thumbnail_height)]

    """
    return (
        getattr(field_file, 'instance', None),
        getattr(getattr(field_file, 'field', None), 'attname', None),
    )


def generate(generator):
    """
    Calls the ``generate()`` method of a generator instance, and then wraps the
    result in a Django File object so Django knows how to save it.

    """
    content = generator.generate()
    f = File(content)
    # The size of the File must be known or Django will try to open a file
    # without a name and raise an Exception.
    f.size = len(content.read())
    # After getting the size reset the file pointer for future reads.
    content.seek(0)
    return f


def call_strategy_method(file, method_name):
    strategy = getattr(file, 'cachefile_strategy', None)
    fn = getattr(strategy, method_name, None)
    if fn is not None:
        fn(file)


def get_cache():
    try:
        from django.core.cache import caches
    except ImportError:
        # Django < 1.7
        from django.core.cache import get_cache
        return get_cache(settings.IMAGEKIT_CACHE_BACKEND)

    return caches[settings.IMAGEKIT_CACHE_BACKEND]


def sanitize_cache_key(key):
    if settings.IMAGEKIT_USE_MEMCACHED_SAFE_CACHE_KEY:
        # Memcached keys can't contain whitespace or control characters.
        new_key = bad_memcached_key_chars.sub('', key)

        # The also can't be > 250 chars long. Since we don't know what the
        # user's cache ``KEY_FUNCTION`` setting is like, we'll limit it to 200.
        if len(new_key) >= 200:
            new_key = '%s:%s' % (new_key[:200-33], md5(force_bytes(key)).hexdigest())

        key = new_key
    return key
