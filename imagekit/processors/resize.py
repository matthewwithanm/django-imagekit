from imagekit.lib import Image
from .crop import Crop as _Crop, SmartCrop as _SmartCrop
import warnings


class Resize(object):
    pass

class Fill(object):
    """
    Resizes an image , cropping it to the exact specified width and height.

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
        :param anchor: Specifies which part of the image should be retained
            when cropping. Valid values are:

            - Fill.TOP_LEFT
            - Fill.TOP
            - Fill.TOP_RIGHT
            - Fill.LEFT
            - Fill.CENTER
            - Fill.RIGHT
            - Fill.BOTTOM_LEFT
            - Fill.BOTTOM
            - Fill.BOTTOM_RIGHT

        """
        self.width = width
        self.height = height
        self.anchor = anchor

    def process(self, img):
        cur_width, cur_height = img.size
        horizontal_anchor, vertical_anchor = Fill._ANCHOR_PTS[self.anchor or \
                Fill.CENTER]
        ratio = max(float(self.width) / cur_width, float(self.height) / cur_height)
        resize_x, resize_y = ((cur_width * ratio), (cur_height * ratio))
        crop_x, crop_y = (abs(self.width - resize_x), abs(self.height - resize_y))
        x_diff, y_diff = (int(crop_x / 2), int(crop_y / 2))
        box_left, box_right = {
            0: (0, self.width),
            0.5: (int(x_diff), int(x_diff + self.width)),
            1: (int(crop_x), int(resize_x)),
        }[horizontal_anchor]
        box_upper, box_lower = {
            0: (0, self.height),
            0.5: (int(y_diff), int(y_diff + self.height)),
            1: (int(crop_y), int(resize_y)),
        }[vertical_anchor]
        box = (box_left, box_upper, box_right, box_lower)
        img = img.resize((int(resize_x), int(resize_y)), Image.ANTIALIAS).crop(box)
        return img


class Crop(Fill):
    def __init__(self, *args, **kwargs):
        warnings.warn('`imagekit.processors.resize.Crop` has been renamed to'
                '`imagekit.processors.resize.Fill`.', DeprecationWarning)
        super(Crop, self).__init__(*args, **kwargs)


class Fit(object):
    """
    Resizes an image to fit within the specified dimensions.

    """
    def __init__(self, width=None, height=None, upscale=None, mat_color=None):
        """
        :param width: The maximum width of the desired image.
        :param height: The maximum height of the desired image.
        :param upscale: A boolean value specifying whether the image should
            be enlarged if its dimensions are smaller than the target
            dimensions.
        :param mat_color: If set, the target image size will be enforced and
            the specified color will be used as background color to pad the image.

        """
        self.width = width
        self.height = height
        self.upscale = upscale
        self.mat_color = mat_color

    def process(self, img):
        cur_width, cur_height = img.size
        if not self.width is None and not self.height is None:
            ratio = min(float(self.width) / cur_width,
                    float(self.height) / cur_height)
        else:
            if self.width is None:
                ratio = float(self.height) / cur_height
            else:
                ratio = float(self.width) / cur_width
        new_dimensions = (int(round(cur_width * ratio)),
                          int(round(cur_height * ratio)))
        if (cur_width > new_dimensions[0] or cur_height > new_dimensions[1]) or \
            self.upscale:
                img = img.resize(new_dimensions, Image.ANTIALIAS)
        if self.mat_color:
            new_img = Image.new('RGBA', (self.width, self.height),  self.mat_color)
            new_img.paste(img, ((self.width - img.size[0]) / 2, (self.height - img.size[1]) / 2))
            img = new_img
        return img


class Crop(_Crop):
    def __init__(self, *args, **kwargs):
        warnings.warn('The Crop processor has been moved to'
                ' `imagekit.processors.crop.Crop`, where it belongs.',
                DeprecationWarning)
        super(SmartCrop, self).__init__(*args, **kwargs)

class SmartCrop(_SmartCrop):
    def __init__(self, *args, **kwargs):
        warnings.warn('The SmartCrop processor has been moved to'
                ' `imagekit.processors.crop.SmartCrop`, where it belongs.',
                DeprecationWarning)
        super(SmartCrop, self).__init__(*args, **kwargs)
