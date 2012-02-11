from imagekit.lib import Image
from . import crop
import warnings


class BasicResize(object):
    """
    Resizes an image to the specified width and height.

    """
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def process(self, img):
        return img.resize((self.width, self.height), Image.ANTIALIAS)


class Cover(object):
    """
    Resizes the image to the smallest possible size that will entirely cover the
    provided dimensions. You probably won't be using this processor directly,
    but it's used internally by ``Fill`` and ``SmartFill``.

    """
    def __init__(self, width, height):
        self.width, self.height = width, height

    def process(self, img):
        original_width, original_height = img.size
        ratio = max(float(self.width) / original_width,
                float(self.height) / original_height)
        new_width, new_height = (int(original_width * ratio),
                int(original_height * ratio))
        return img.resize((new_width, new_height), Image.ANTIALIAS)


class Fill(object):
    """
    Resizes an image , cropping it to the exact specified width and height.

    """
    TOP_LEFT = crop.Crop.TOP_LEFT
    TOP = crop.Crop.TOP
    TOP_RIGHT = crop.Crop.TOP_RIGHT
    BOTTOM_LEFT = crop.Crop.BOTTOM_LEFT
    BOTTOM = crop.Crop.BOTTOM
    BOTTOM_RIGHT = crop.Crop.BOTTOM_RIGHT
    CENTER = crop.Crop.CENTER
    LEFT = crop.Crop.LEFT
    RIGHT = crop.Crop.RIGHT

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
        img = Cover(self.width, self.height).process(img)
        return crop.Crop(self.width, self.height,
                anchor=self.anchor).process(img)


class SmartFill(object):
    """
    The ``SmartFill`` processor is identical to ``Fill``, except that it uses
    entropy to crop the image instead of a user-specified anchor point.
    Internally, it simply runs the ``resize.Cover`` and ``crop.SmartCrop``
    processors in series.

    """
    def __init__(self, width, height):
        self.width, self.height = width, height

    def process(self, img):
        img = Cover(self.width, self.height).process(img)
        return crop.SmartCrop(self.width, self.height).process(img)


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


class SmartCrop(crop.SmartCrop):
    def __init__(self, *args, **kwargs):
        warnings.warn('The SmartCrop processor has been moved to'
                ' `imagekit.processors.crop.SmartCrop`, where it belongs.',
                DeprecationWarning)
        super(SmartCrop, self).__init__(*args, **kwargs)
