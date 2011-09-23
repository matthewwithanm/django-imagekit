""" ImageKit utility functions """

import tempfile

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
