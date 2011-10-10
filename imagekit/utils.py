""" ImageKit utility functions """

import tempfile


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
