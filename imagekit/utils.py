""" ImageKit utility functions """

import tempfile, hashlib

def img_to_fobj(img, format, **kwargs):
    tmp = tempfile.TemporaryFile()
    img.save(tmp, format, **kwargs)
    tmp.seek(0)
    return tmp


def pil_for_lut(lut):
    """
    make a PIL image from an RGB LUT of format:
    [
        (r,g,b),
        (r,g,b),
        ...
    ]
    where r, g, b are 0-255. 
    
    """
    from imagekit.lib import Image, ImageCms
    
    outlut = Image.new('RGB', (1, len(lut)+2))
    outpix = outlut.load()
    
    for p in range(len(lut)):
        outpix[0,p] = lut[p]
    
    return outlut
