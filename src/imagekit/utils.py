""" ImageKit utility functions """

import tempfile

def img_to_fobj(img, format, **kwargs):
    tmp = tempfile.TemporaryFile()
    if format != 'JPEG':
        try:
            img.save(tmp, format, **kwargs)
            return
        except KeyError:
            pass
    img.save(tmp, format, **kwargs)
    tmp.seek(0)
    return tmp
