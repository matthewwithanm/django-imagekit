"""Imagekit image processors.

A processor accepts an image, does some stuff, and returns the result.
Processors can do anything with the image you want, but their responsibilities
should be limited to image manipulations--they should be completely decoupled
from both the filesystem and the ORM.

"""
from imagekit.lib import *


class ProcessorPipeline(list):
    """A :class:`list` of other processors. This class allows any object that
    knows how to deal with a single processor to deal with a list of them.
    For example::

        processed_image = ProcessorPipeline([ProcessorA(), ProcessorB()]).process(image)

    """
    def process(self, img):
        for proc in self:
            img = proc.process(img)
        return img


class Adjust(object):
    """Performs color, brightness, contrast, and sharpness enhancements on the
    image. See :mod:`PIL.ImageEnhance` for more imformation.

    """
    def __init__(self, color=1.0, brightness=1.0, contrast=1.0, sharpness=1.0):
        """
        :param color: A number between 0 and 1 that specifies the saturation of
                the image. 0 corresponds to a completely desaturated image
                (black and white) and 1 to the original color.
                See :class:`PIL.ImageEnhance.Color`
        :param brightness: A number representing the brightness; 0 results in a
                completely black image whereas 1 corresponds to the brightness
                of the original. See :class:`PIL.ImageEnhance.Brightness`
        :param contrast: A number representing the contrast; 0 results in a
                completely gray image whereas 1 corresponds to the contrast of
                the original. See :class:`PIL.ImageEnhance.Contrast`
        :param sharpness: A number representing the sharpness; 0 results in a
                blurred image; 1 corresponds to the original sharpness; 2
                results in a sharpened image. See
                :class:`PIL.ImageEnhance.Sharpness`
        
        """
        self.color = color
        self.brightness = brightness
        self.contrast = contrast
        self.sharpness = sharpness

    def process(self, img):
        img = img.convert('RGB')
        for name in ['Color', 'Brightness', 'Contrast', 'Sharpness']:
            factor = getattr(self, name.lower())
            if factor != 1.0:
                try:
                    img = getattr(ImageEnhance, name)(img).enhance(factor)
                except ValueError:
                    pass
        return img


class Reflection(object):
    """Creates an image with a reflection.
    
    """
    background_color = '#FFFFFF'
    size = 0.0
    opacity = 0.6

    def process(self, img):
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
        # return the image complete with reflection effect
        return composite


class _Resize(object):
    
    width = None
    height = None
    
    def __init__(self, width=None, height=None):
        if width is not None:
            self.width = width
        if height is not None:
            self.height = height

    def process(self, img):
        raise NotImplementedError('process must be overridden by subclasses.')


class Crop(_Resize):
    """Resizes an image , cropping it to the specified width and height.

    """

    TOP_LEFT = 'tl'
    TOP = 't'
    TOP_RIGHT = 'tr'
    BOTTOM_LEFT = 'bl'
    BOTTOM = 'b'
    BOTTOM_RIGHT = 'br'
    CENTER = 'c'
    LEFT = 'l'
    RIGHT = 'r'

    _ANCHOR_PTS = {
        TOP_LEFT: (0, 0),
        TOP: (0.5, 0),
        TOP_RIGHT: (1, 0),
        LEFT: (0, 0.5),
        CENTER: (0.5, 0.5),
        RIGHT: (1, 0.5),
        BOTTOM_LEFT: (0, 1),
        BOTTOM: (0.5, 1),
        BOTTOM_RIGHT: (1, 1),
    }

    def __init__(self, width=None, height=None, anchor=None):
        """
        :param width: The target width, in pixels.
        :param height: The target height, in pixels.
        :param anchor: Specifies which part of the image should be retained when
            cropping. Valid values are:

            - Crop.TOP_LEFT
            - Crop.TOP
            - Crop.TOP_RIGHT
            - Crop.LEFT
            - Crop.CENTER
            - Crop.RIGHT
            - Crop.BOTTOM_LEFT
            - Crop.BOTTOM
            - Crop.BOTTOM_RIGHT

        """
        super(Crop, self).__init__(width, height)
        self.anchor = anchor

    def process(self, img):
        cur_width, cur_height = img.size
        horizontal_anchor, vertical_anchor = Crop._ANCHOR_PTS[self.anchor or \
                Crop.CENTER]
        ratio = max(float(self.width)/cur_width, float(self.height)/cur_height)
        resize_x, resize_y = ((cur_width * ratio), (cur_height * ratio))
        crop_x, crop_y = (abs(self.width - resize_x), abs(self.height - resize_y))
        x_diff, y_diff = (int(crop_x / 2), int(crop_y / 2))
        box_left, box_right = {
            0:   (0, self.width),
            0.5: (int(x_diff), int(x_diff + self.width)),
            1:   (int(crop_x), int(resize_x)),
        }[horizontal_anchor]
        box_upper, box_lower = {
            0:   (0, self.height),
            0.5: (int(y_diff), int(y_diff + self.height)),
            1:   (int(crop_y), int(resize_y)),
        }[vertical_anchor]
        box = (box_left, box_upper, box_right, box_lower)
        img = img.resize((int(resize_x), int(resize_y)), Image.ANTIALIAS).crop(box)
        return img


class Fit(_Resize):
    """Resizes an image to fit within the specified dimensions.

    """
    
    def __init__(self, width=None, height=None, upscale=None):
        """
        :param width: The maximum width of the desired image.
        :param height: The maximum height of the desired image.
        :param upscale: A boolean value specifying whether the image should be
                enlarged if its dimensions are smaller than the target
                dimensions.

        """
        super(Fit, self).__init__(width, height)
        self.upscale = upscale

    def process(self, img):
        cur_width, cur_height = img.size
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
                return img
        img = img.resize(new_dimensions, Image.ANTIALIAS)
        return img


class Transpose(object):
    """ Rotates or flips the image

    """
    AUTO = 'auto'
    FLIP_HORIZONTAL = Image.FLIP_LEFT_RIGHT
    FLIP_VERTICAL = Image.FLIP_TOP_BOTTOM
    ROTATE_90 = Image.ROTATE_90
    ROTATE_180 = Image.ROTATE_180
    ROTATE_270 = Image.ROTATE_270

    methods = [AUTO]
    _EXIF_ORIENTATION_STEPS = {
        1: [],
        2: [FLIP_HORIZONTAL],
        3: [ROTATE_180],
        4: [FLIP_VERTICAL],
        5: [ROTATE_270, FLIP_HORIZONTAL],
        6: [ROTATE_270],
        7: [ROTATE_90, FLIP_HORIZONTAL],
        8: [ROTATE_90],
    }

    def __init__(self, *args):
        """
        Possible arguments:
            - Transpose.AUTO 
            - Transpose.FLIP_HORIZONTAL
            - Transpose.FLIP_VERTICAL
            - Transpose.ROTATE_90
            - Transpose.ROTATE_180
            - Transpose.ROTATE_270

        The order of the arguments dictates the order in which the Transposition
        steps are taken.

        If Transpose.AUTO is present, all other arguments are ignored, and the 
        processor will attempt to rotate the image according to the 
        EXIF Orientation data.

        """
        super(Transpose, self).__init__()
        if args:
            self.methods = args

    def process(self, img):
        if self.AUTO in self.methods:
            try:
                orientation = img._getexif()[0x0112]
                ops = self._EXIF_ORIENTATION_STEPS[orientation]
            except AttributeError:
                ops = []
        else:
            ops = self.methods
        for method in ops:
            img = img.transpose(method)
        return img
