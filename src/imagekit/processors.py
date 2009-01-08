""" Imagekit Image "ImageProcessors"

A processor defines a set of class variables (optional) and a 
class method named "process" which processes the supplied image using
the class properties as settings. The process method can be overridden as well allowing user to define their
own effects/processes entirely.

"""
from imagekit import *

class ImageProcessor(object):
    """ Base image processor class """
    @classmethod
    def process(cls, image, obj):
        return image


class Resize(ImageProcessor):
    width = None
    height = None
    crop = False
    upscale = False
    
    @classmethod
    def process(cls, image, obj):
        cur_width, cur_height = image.size
        if cls.crop:
            crop_horz = getattr(obj, obj._ik.crop_horz_field, 1)
            crop_vert = getattr(obj, obj._ik.crop_vert_field, 1)
            ratio = max(float(cls.width)/cur_width, float(cls.height)/cur_height)
            resize_x, resize_y = ((cur_width * ratio), (cur_height * ratio))
            crop_x, crop_y = (abs(cls.width - resize_x), abs(cls.height - resize_y))
            x_diff, y_diff = (int(crop_x / 2), int(crop_y / 2))
            box_left, box_right = {
                0: (0, cls.width),
                1: (int(x_diff), int(x_diff + cls.width)),
                2: (int(crop_x), int(resize_x)),
            }[crop_horz]
            box_upper, box_lower = {
                0: (0, cls.height),
                1: (int(y_diff), int(y_diff + cls.height)),
                2: (int(crop_y), int(resize_y)),
            }[crop_vert]
            box = (box_left, box_upper, box_right, box_lower)
            image = image.resize((int(resize_x), int(resize_y)), Image.ANTIALIAS).crop(box)
        else:
            if not cls.width is None and not cls.height is None:
                ratio = min(float(cls.width)/cur_width,
                            float(cls.height)/cur_height)
            else:
                if cls.width is None:
                    ratio = float(cls.height)/cur_height
                else:
                    ratio = float(cls.width)/cur_width
            new_dimensions = (int(round(cur_width*ratio)),
                              int(round(cur_height*ratio)))
            if new_dimensions[0] > cur_width or \
               new_dimensions[1] > cur_height:
                if not cls.upscale:
                    return image
            image = image.resize(new_dimensions, Image.ANTIALIAS)
        return image

    
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
    def process(cls, image, obj):
        return image.transpose(getattr(Image, cls.method))        

    
class Adjustment(ImageProcessor):
    color = 1.0
    brightness = 1.0
    contrast = 1.0
    sharpness = 1.0

    @classmethod
    def process(cls, image, obj):
        for name in ['Color', 'Brightness', 'Contrast', 'Sharpness']:
            factor = getattr(cls, name.lower())
            if factor != 1.0:
                image = getattr(ImageEnhance, name)(image).enhance(factor)
        return image


class Reflection(ImageProcessor):
    background_color = '#fffff'
    size = 0.0
    opacity = 0.6
