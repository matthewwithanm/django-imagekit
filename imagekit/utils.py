import logging
from tempfile import NamedTemporaryFile

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files import File
from django.utils.importlib import import_module
from hashlib import md5
from pilkit.utils import *
import re
from .lib import NullHandler


bad_memcached_key_chars = re.compile(ur'[\u0000-\u001f\s]+')


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
    except ImportError, e:
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

    from django.conf import settings
    from django.utils.importlib import import_module
    from django.utils.module_loading import module_has_submodule

    for app in settings.INSTALLED_APPS:
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

    # If the file doesn't have a name, Django will raise an Exception while
    # trying to save it, so we create a named temporary file.
    if not getattr(content, 'name', None):
        f = NamedTemporaryFile()
        f.write(content.read())
        f.seek(0)
        content = f

    return File(content)


def call_strategy_method(file, method_name):
    strategy = getattr(file, 'cachefile_strategy', None)
    fn = getattr(strategy, method_name, None)
    if fn is not None:
        fn(file)


def sanitize_cache_key(key):
    if settings.IMAGEKIT_USE_MEMCACHED_SAFE_CACHE_KEY:
        # Memcached keys can't contain whitespace or control characters.
        new_key = bad_memcached_key_chars.sub('', key)

        # The also can't be > 250 chars long. Since we don't know what the
        # user's cache ``KEY_FUNCTION`` setting is like, we'll limit it to 200.
        if len(new_key) >= 200:
            new_key = '%s:%s' % (new_key[:200-33], md5(key).hexdigest())

        key = new_key
    return key
