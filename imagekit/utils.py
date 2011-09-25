""" ImageKit utility functions """

import tempfile, types
from django.utils.functional import wraps
from lib import Image


def img_to_fobj(img, format, **kwargs):
    tmp = tempfile.TemporaryFile()
    img.convert('RGB').save(tmp, format, **kwargs)
    tmp.seek(0)
    return tmp


def get_spec_files(instance):
    from imagekit.models import ImageSpecFile
    spec_files = []
    for key in dir(instance):
        try:
            value = getattr(instance, key)
        except AttributeError:
            continue
        if isinstance(value, ImageSpecFile):
            spec_files.append(value)
    return spec_files


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

