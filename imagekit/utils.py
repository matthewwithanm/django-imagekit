import tempfile
import types

from django.utils.functional import wraps

from imagekit.lib import Image


def img_to_fobj(img, format, **kwargs):
    tmp = tempfile.TemporaryFile()

    # Preserve transparency if the image is in Pallette (P) mode.
    if img.mode == 'P':
        kwargs['transparency'] = len(img.split()[-1].getcolors())
    else:
        img.convert('RGB')

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
