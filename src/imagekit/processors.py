""" Imagekit Image "ImageProcessors"

A processor defines a set of class variables (optional) and a 
class method named "process" which processes the supplied image using
the class properties as settings. The process method can be overridden as well allowing user to define their
own effects/processes entirely.

"""

class ImageProcessor(object):
    """ Base image processor class """
    @classmethod
    def process(cls, image):
        return image


class Resize(ImageProcessor):
    width = None
    height = None
    crop = False
    upscale = False
    
    
class Transpose(ImageProcessor):
    """ Rotates or flips the image
    
    Method choices:
        - FLIP_LEFT RIGHT
        - FLIP_TOP_BOTTOM
        - ROTATE_90
        - ROTATE_270
        - ROTATE_180
        
    """
    method = 'FLIP_LEFT_RIGHT'
    
    @classmethod
    def process(cls, image):
        return image.transpose(getattr(Image, cls.method))        

    
class Adjustment(ImageProcessor):
    color = 1.0
    brightness = 1.0
    contrast = 1.0
    sharpness = 1.0

    @classmethod
    def process(cls, image):
        for name in ['Color', 'Brightness', 'Contrast', 'Sharpness']:
            factor = getattr(cls, name.lower())
            if factor != 1.0:
                image = getattr(ImageEnhance, name)(image).enhance(factor)
        return image


class Reflection(ImageProcessor):
    background_color = '#fffff'
    size = 0.0
    opacity = 0.6
