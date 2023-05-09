import logging
import re
from hashlib import md5
from importlib import import_module

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files import File
from pilkit.utils import *

bad_memcached_key_chars = re.compile('[\u0000-\u001f\\s]+')

_autodiscovered = False


def get_nonabstract_descendants(model):
    """ Returns all non-abstract descendants of the model. """
    if not model._meta.abstract:
        yield model
    for s in model.__subclasses__():
        yield from get_nonabstract_descendants(s)


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

    from django.utils.module_loading import autodiscover_modules
    autodiscover_modules('imagegenerators')
    _autodiscovered = True


def get_logger(logger_name='imagekit', add_null_handler=True):
    logger = logging.getLogger(logger_name)
    if add_null_handler:
        logger.addHandler(logging.NullHandler())
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
    from django.core.cache import caches

    return caches[settings.IMAGEKIT_CACHE_BACKEND]


def get_storage():
    try:
        from django.core.files.storage import storages, InvalidStorageError
    except ImportError:  # Django < 4.2
        return get_singleton(
            settings.IMAGEKIT_DEFAULT_FILE_STORAGE, 'file storage backend'
        )
    else:
        try:
            return storages[settings.IMAGEKIT_DEFAULT_FILE_STORAGE]
        except InvalidStorageError:
            return get_singleton(
                settings.IMAGEKIT_DEFAULT_FILE_STORAGE, 'file storage backend'
            )


def sanitize_cache_key(key):
    if settings.IMAGEKIT_USE_MEMCACHED_SAFE_CACHE_KEY:
        # Memcached keys can't contain whitespace or control characters.
        new_key = bad_memcached_key_chars.sub('', key)

        # The also can't be > 250 chars long. Since we don't know what the
        # user's cache ``KEY_FUNCTION`` setting is like, we'll limit it to 200.
        if len(new_key) >= 200:
            new_key = '%s:%s' % (new_key[:200 - 33], md5(key.encode('utf-8')).hexdigest())

        key = new_key
    return key
