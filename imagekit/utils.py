import os
import tempfile
import types

from django.utils.functional import wraps

from imagekit.lib import Image, ImageFile


RGBA_TRANSPARENCY_FORMATS = ['PNG']
PALETTE_TRANSPARENCY_FORMATS = ['PNG', 'GIF']


def img_to_fobj(img, format, **kwargs):
    # Attempt to preserve transparency.
    matte = False
    if img.mode == 'RGBA':
        if format in RGBA_TRANSPARENCY_FORMATS:
            pass
        elif format in PALETTE_TRANSPARENCY_FORMATS:
            # If you're going from a format with alpha transparency to one with
            # palette transparency, transparency values will be snapped: pixels
            # that are more opaque than not will become fully opaque; pixels
            # that are more transparent than not will become fully transparent.
            # This will not produce a good-looking result if your image contains
            # varying levels of opacity; in that case, you'll probably want to
            # use a processor to matte the image on a solid color. The reason we
            # don't matte by default is because not doing so allows processors
            # to treat RGBA-format images as a super-type of P-format images: if
            # you have an RGBA-format image with only a single transparent
            # color, and save it as a GIF, it will retain its transparency. In
            # other words, a P-format image converted to an RGBA-formatted image
            # by a processor and then saved as a P-format image will give the
            # expected results.
            alpha = img.split()[-1]
            mask = Image.eval(alpha, lambda a: 255 if a <= 128 else 0)
            img = img.convert('RGB').convert('P', palette=Image.ADAPTIVE,
                    colors=255)
            img.paste(255, mask)
            kwargs['transparency'] = 255
        else:
            # Simply converting an RGBA-format image to an RGB one creates a
            # gross result, so we matte the image on a white background. If
            # that's not what you want, that's fine: use a processor to deal
            # with the transparency however you want. This is simply a sensible
            # default that will always produce something that looks good. Or at
            # least, it will look better than just a straight conversion.
            matte = True
    elif img.mode == 'P':
        if format in PALETTE_TRANSPARENCY_FORMATS:
            kwargs['transparency'] = img.info['transparency']
        elif format in RGBA_TRANSPARENCY_FORMATS:
            # Currently PIL doesn't support any RGBA-mode formats that aren't
            # also P-mode formats, so this will never happen.
            img = img.convert('RGBA')
        else:
            matte = True
    else:
        img = img.convert('RGB')

        # GIFs are always going to be in palette mode, so we can do a little
        # optimization. Note that the RGBA sources also use adaptive
        # quantization (above). Images that are already in P mode don't need any
        # quantization because their colors are already limited.
        if format == 'GIF':
            img = img.convert('P', palette=Image.ADAPTIVE)

    if matte:
        img = img.convert('RGBA')
        bg = Image.new('RGBA', img.size, (255, 255, 255))
        bg.paste(img, img)
        img = bg.convert('RGB')

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
        ik = getattr(instance, '_ik')
    except AttributeError:
        return []
    else:
        return [getattr(instance, n) for n in ik.spec_file_names]


def open_image(target):
    if hasattr(target, 'mode') and 'w' in target.mode and os.path.exists(target.name):
        # target is a file like object with write mode enabled
        # PIL will zero this file out and then give and IO error
        # instead just pass PIL the path
        target = target.name
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
