""" ImageKit utility functions """

import tempfile

def img_to_fobj(img, format, **kwargs):
    tmp = tempfile.TemporaryFile()
    
    #preserve transparency if the image is in Pallette (P) mode
    if img.mode == 'P':
        #assert False, img.info
        kwargs['transparency'] = 255
    else:
        img.convert('RGB')
    
    img.save(tmp, format, **kwargs)
    tmp.seek(0)
    return tmp
