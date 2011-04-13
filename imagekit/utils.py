""" ImageKit utility functions """

import tempfile, hashlib

def img_to_fobj(img, format, **kwargs):
    tmp = tempfile.TemporaryFile()
    img.save(tmp, format, **kwargs)
    tmp.seek(0)
    return tmp


def icc_to_fobj(imgmodl, format='icc', **kwargs):
    tmp = tempfile.TemporaryFile(mode="w+b", suffix=format)
    tmp.write(imgmodl._get_iccstr())
    tmp.flush()
    tmp.seek(0)
    return tmp


def yield_fake_name(suf='icc'):
    return os.path.join(
        tempfile._candidate_tempdir_list()[0],
        "%s.%s" % (
            tempfile._name_sequence.next(),
            suf
        ))

# from http://stackoverflow.com/questions/1131220/get-md5-hash-of-a-files-without-open-it-in-python
def md5_for_file(f, block_size=2**20):
    md5 = hashlib.md5()
    while True:
        data = f.read(block_size)
        if not data:
            break
        md5.update(data)
    return md5.hexdigest()



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
