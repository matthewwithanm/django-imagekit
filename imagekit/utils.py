import tempfile
import types

from django.db.models.loading import cache
from django.utils.functional import wraps

from .imagecache import get_default_image_cache_backend
from .lib import Image, ImageFile


def img_to_fobj(img, format, **kwargs):
    tmp = tempfile.TemporaryFile()
    try:
        img.save(tmp, format, **kwargs)
    except IOError:
        # PIL can have problems saving large JPEGs if MAXBLOCK isn't big enough,
        # So if we have a problem saving, we temporarily increase it. See
        # http://github.com/jdriscoll/django-imagekit/issues/50
        old_maxblock = ImageFile.MAXBLOCK
        ImageFile.MAXBLOCK = img.size[0] * img.size[1]
        try:
            img.save(tmp, format, **kwargs)
        finally:
            ImageFile.MAXBLOCK = old_maxblock
    tmp.seek(0)
    return tmp


def get_spec_files(instance):
    try:
        return instance._ik.spec_files
    except AttributeError:
        return []


def open_image(target):
    target.seek(0)
    img = Image.open(target)
    img.copy = types.MethodType(_wrap_copy(img.copy), img, img.__class__)
    return img


def _wrap_copy(f):
    @wraps(f)
    def copy(self):
        img = f()
        try:
            img.app = self.app
        except AttributeError:
            pass
        try:
            img._getexif = self._getexif
        except AttributeError:
            pass
        return img
    return copy


class UnknownExtensionError(Exception):
    pass


class UnknownFormatError(Exception):
    pass


_pil_init = 0


def _preinit_pil():
    """Loads the standard PIL file format drivers. Returns True if ``preinit()``
    was called (and there's a potential that more drivers were loaded) or False
    if there is no possibility that new drivers were loaded.

    """
    global _pil_init
    if _pil_init < 1:
        Image.preinit()
        _pil_init = 1
        return True
    return False


def _init_pil():
    """Loads all PIL file format drivers. Returns True if ``init()`` was called
    (and there's a potential that more drivers were loaded) or False if there is
    no possibility that new drivers were loaded.

    """
    global _pil_init
    _preinit_pil()
    if _pil_init < 2:
        Image.init()
        _pil_init = 2
        return True
    return False


def _extension_to_format(extension):
    return Image.EXTENSION.get(extension.lower())


def _format_to_extension(format):
    if format:
        for k, v in Image.EXTENSION.iteritems():
            if v == format.upper():
                return k
    return None


def extension_to_format(extension):
    """Returns the format that corresponds to the provided extension.

    """
    format = _extension_to_format(extension)
    if not format and _preinit_pil():
        format = _extension_to_format(extension)
    if not format and _init_pil():
        format = _extension_to_format(extension)
    if not format:
        raise UnknownExtensionError(extension)
    return format


def format_to_extension(format):
    """Returns the first extension that matches the provided format.

    """
    extension = None
    if format:
        extension = _format_to_extension(format)
        if not extension and _preinit_pil():
            extension = _format_to_extension(format)
        if not extension and _init_pil():
            extension = _format_to_extension(format)
    if not extension:
        raise UnknownFormatError(format)
    return extension


def _get_models(apps):
    models = []
    for app_label in apps or []:
        app = cache.get_app(app_label)
        models += [m for m in cache.get_models(app)]
    return models


def invalidate_app_cache(apps):
    for model in _get_models(apps):
        print 'Invalidating cache for "%s.%s"' % (model._meta.app_label, model.__name__)
        for obj in model._default_manager.order_by('-pk'):
            for f in get_spec_files(obj):
                f.invalidate()


def validate_app_cache(apps, force_revalidation=False):
    for model in _get_models(apps):
        for obj in model._default_manager.order_by('-pk'):
            model_name = '%s.%s' % (model._meta.app_label, model.__name__)
            if force_revalidation:
                print 'Invalidating & validating cache for "%s"' % model_name
            else:
                print 'Validating cache for "%s"' % model_name
            for f in get_spec_files(obj):
                if force_revalidation:
                    f.invalidate()
                f.validate()


def autodiscover():
    """
    Auto-discover INSTALLED_APPS imagespecs.py modules and fail silently when
    not present. This forces an import on them to register any admin bits they
    may want.

    Copied from django.contrib.admin
    """

    import copy
    from django.conf import settings
    from django.utils.importlib import import_module
    from django.utils.module_loading import module_has_submodule
    from .templatetags import imagekit_tags

    for app in settings.INSTALLED_APPS:
        mod = import_module(app)
        # Attempt to import the app's admin module.
        try:
            import_module('%s.imagespecs' % app)
        except:
            # Decide whether to bubble up this error. If the app just
            # doesn't have an admin module, we can ignore the error
            # attempting to import it, otherwise we want it to bubble up.
            if module_has_submodule(mod, 'imagespecs'):
                raise


class SpecWrapper(object):
    """
    Wraps a user-defined spec object so we can access properties that don't
    exist without errors.

    """
    def __init__(self, spec):
        self.processors = getattr(spec, 'processors', None)
        self.format = getattr(spec, 'format', None)
        self.options = getattr(spec, 'options', None)
        self.autoconvert = getattr(spec, 'autoconvert', True)
        self.storage = getattr(spec, 'storage', None)
        self.image_cache_backend = getattr(spec, 'image_cache_backend', None) \
                or get_default_image_cache_backend()
