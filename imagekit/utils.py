import tempfile
import types

from django.utils.functional import wraps

from imagekit.lib import Image


def img_to_fobj(img, format, **kwargs):
    tmp = tempfile.TemporaryFile()

    # Preserve transparency if the image is in Pallette (P) mode.
    transparency_formats = ('PNG', 'GIF', )
    if img.mode == 'P' and format in transparency_formats:
        kwargs['transparency'] = len(img.split()[-1].getcolors())
    else:
        img = img.convert('RGB')

    img.save(tmp, format, **kwargs)
    tmp.seek(0)
    return tmp


def get_spec_files(instance):
    try:
        ik = getattr(instance, '_ik')
    except AttributeError:
        return []
    else:
        return [getattr(instance, n) for n in ik.spec_file_names]


def open_image(target):
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
    extension = _format_to_extension(format)
    if not extension and _preinit_pil():
        extension = _format_to_extension(format)
    if not extension and _init_pil():
        extension = _format_to_extension(format)
    if not extension:
        raise UnknownFormatError(format)
    return extension
