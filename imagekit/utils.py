""" ImageKit utility functions """

import tempfile

def img_to_fobj(img, format, **kwargs):
    tmp = tempfile.TemporaryFile()
    img.convert('RGB').save(tmp, format, **kwargs)
    tmp.seek(0)
    return tmp
