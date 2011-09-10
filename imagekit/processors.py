""" Imagekit Image "ImageProcessors"

A processor defines a set of class variables (optional) and a
class method named "process" which processes the supplied image using
the class properties as settings. The process method can be overridden as well allowing user to define their
own effects/processes entirely.

"""
from imagekit.lib import *

class ImageProcessor(object):
    """ Base image processor class """

    def process(self, img, fmt, obj, spec):
        return img, fmt


class Adjust(ImageProcessor):
    
    def __init__(self, color=1.0, brightness=1.0, contrast=1.0, sharpness=1.0):
        self.color = color
        self.brightness = brightness
        self.contrast = contrast
        self.sharpness = sharpness

    def process(self, img, fmt, obj, spec):
        img = img.convert('RGB')
        for name in ['Color', 'Brightness', 'Contrast', 'Sharpness']:
            factor = getattr(self, name.lower())
            if factor != 1.0:
                try:
                    img = getattr(ImageEnhance, name)(img).enhance(factor)
                except ValueError:
                    pass
        return img, fmt


class Format(ImageProcessor):
    format = 'JPEG'
    extension = 'jpg'

    def process(self, img, fmt, obj, spec):
        return img, self.format


class Reflection(ImageProcessor):
    background_color = '#FFFFFF'
    size = 0.0
    opacity = 0.6

    def process(self, img, fmt, obj, spec):
        # convert bgcolor string to rgb value
        background_color = ImageColor.getrgb(self.background_color)
        # handle palleted images
        img = img.convert('RGB')
        # copy orignial image and flip the orientation
        reflection = img.copy().transpose(Image.FLIP_TOP_BOTTOM)
        # create a new image filled with the bgcolor the same size
        background = Image.new("RGB", img.size, background_color)
        # calculate our alpha mask
        start = int(255 - (255 * self.opacity)) # The start of our gradient
        steps = int(255 * self.size) # the number of intermedite values
        increment = (255 - start) / float(steps)
        mask = Image.new('L', (1, 255))
        for y in range(255):
            if y < steps:
                val = int(y * increment + start)
            else:
                val = 255
            mask.putpixel((0, y), val)
        alpha_mask = mask.resize(img.size)
        # merge the reflection onto our background color using the alpha mask
        reflection = Image.composite(background, reflection, alpha_mask)
        # crop the reflection
        reflection_height = int(img.size[1] * self.size)
        reflection = reflection.crop((0, 0, img.size[0], reflection_height))
        # create new image sized to hold both the original image and the reflection
        composite = Image.new("RGB", (img.size[0], img.size[1]+reflection_height), background_color)
        # paste the orignal image and the reflection into the composite image
        composite.paste(img, (0, 0))
        composite.paste(reflection, (0, img.size[1]))
        # Save the file as a JPEG
        fmt = 'JPEG'
        # return the image complete with reflection effect
        return composite, fmt


class _Resize(ImageProcessor):
    
    width = None
    height = None
    crop = False
    upscale = False
    
    def __init__(self, width=None, height=None, crop=None, upscale=None):
        if width is not None:
            self.width = width
        if height is not None:
            self.height = height
        if crop is not None:
            self.crop = crop
        if upscale is not None:
            self.upscale = upscale

    def process(self, img, fmt, obj, spec):
        cur_width, cur_height = img.size
        if self.crop:
            crop_horz = getattr(obj, obj._ik.crop_horz_field, 1)
            crop_vert = getattr(obj, obj._ik.crop_vert_field, 1)
            ratio = max(float(self.width)/cur_width, float(self.height)/cur_height)
            resize_x, resize_y = ((cur_width * ratio), (cur_height * ratio))
            crop_x, crop_y = (abs(self.width - resize_x), abs(self.height - resize_y))
            x_diff, y_diff = (int(crop_x / 2), int(crop_y / 2))
            box_left, box_right = {
                0: (0, self.width),
                1: (int(x_diff), int(x_diff + self.width)),
                2: (int(crop_x), int(resize_x)),
            }[crop_horz]
            box_upper, box_lower = {
                0: (0, self.height),
                1: (int(y_diff), int(y_diff + self.height)),
                2: (int(crop_y), int(resize_y)),
            }[crop_vert]
            box = (box_left, box_upper, box_right, box_lower)
            img = img.resize((int(resize_x), int(resize_y)), Image.ANTIALIAS).crop(box)
        else:
            if not self.width is None and not self.height is None:
                ratio = min(float(self.width)/cur_width,
                            float(self.height)/cur_height)
            else:
                if self.width is None:
                    ratio = float(self.height)/cur_height
                else:
                    ratio = float(self.width)/cur_width
            new_dimensions = (int(round(cur_width*ratio)),
                              int(round(cur_height*ratio)))
            if new_dimensions[0] > cur_width or \
               new_dimensions[1] > cur_height:
                if not self.upscale:
                    return img, fmt
            img = img.resize(new_dimensions, Image.ANTIALIAS)
        return img, fmt


class Crop(_Resize):
    def __init__(self, width=None, height=None):
        super(Crop, self).__init__(width, height, crop=True)


class Fit(_Resize):
    def __init__(self, width=None, height=None, upscale=None):
        super(Fit, self).__init__(width, height, crop=False, upscale=upscale)


class Transpose(ImageProcessor):
    """ Rotates or flips the image

    Method should be one of the following strings:
        - FLIP_LEFT RIGHT
        - FLIP_TOP_BOTTOM
        - ROTATE_90
        - ROTATE_270
        - ROTATE_180
        - auto

    If method is set to 'auto' the processor will attempt to rotate the image
    according to the EXIF Orientation data.

    """
    EXIF_ORIENTATION_STEPS = {
        1: [],
        2: ['FLIP_LEFT_RIGHT'],
        3: ['ROTATE_180'],
        4: ['FLIP_TOP_BOTTOM'],
        5: ['ROTATE_270', 'FLIP_LEFT_RIGHT'],
        6: ['ROTATE_270'],
        7: ['ROTATE_90', 'FLIP_LEFT_RIGHT'],
        8: ['ROTATE_90'],
    }

    method = 'auto'

    def process(self, img, fmt, obj, spec):
        if self.method == 'auto':
            try:
                orientation = Image.open(spec._get_imgfield(obj).file)._getexif()[0x0112]
                ops = self.EXIF_ORIENTATION_STEPS[orientation]
            except:
                ops = []
        else:
            ops = [self.method]
        for method in ops:
            img = img.transpose(getattr(Image, method))
        return img, fmt
