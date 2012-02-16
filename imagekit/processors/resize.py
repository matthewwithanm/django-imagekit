from imagekit.lib import Image
from . import crop
import warnings
from . import Anchor


class BasicResize(object):
    """
    Resizes an image to the specified width and height.

    """
    def __init__(self, width, height):
        """
        :param width: The target width, in pixels.
        :param height: The target height, in pixels.

        """
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
        """
        :param width: The target width, in pixels.
        :param height: The target height, in pixels.

        """
        self.width, self.height = width, height

    def process(self, img):
        original_width, original_height = img.size
        ratio = max(float(self.width) / original_width,
                float(self.height) / original_height)
        new_width, new_height = (int(original_width * ratio),
                int(original_height * ratio))
        return BasicResize(new_width, new_height).process(img)


class Fill(object):
    """
    Resizes an image, cropping it to the exact specified width and height.

    """

    def __init__(self, width=None, height=None, anchor=None):
        """
        :param width: The target width, in pixels.
        :param height: The target height, in pixels.
        :param anchor: Specifies which part of the image should be retained
            when cropping.
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
        """
        :param width: The target width, in pixels.
        :param height: The target height, in pixels.

        """
        self.width, self.height = width, height

    def process(self, img):
        img = Cover(self.width, self.height).process(img)
        return crop.SmartCrop(self.width, self.height).process(img)


class Crop(Fill):
    def __init__(self, *args, **kwargs):
        warnings.warn('`imagekit.processors.resize.Crop` has been renamed to'
                '`imagekit.processors.resize.Fill`.', DeprecationWarning)
        super(Crop, self).__init__(*args, **kwargs)


class ResizeCanvas(object):
    """
    Takes an image an resizes the canvas, using a specific background color
    if the new size is larger than the current image.

    """
    def __init__(self, width, height, color=None, top=None, left=None, anchor=None):
        """
        :param width: The target width, in pixels.
        :param height: The target height, in pixels.
        :param color: The background color to use for padding.
        :param anchor: Specifies the relative position of the original image.

        """
        if (anchor and not (top is None and left is None)) \
        or (anchor is None and top is None and left is None):
            raise Exception('You provide either an anchor or x and y position, but not both or none.')
        self.width = width
        self.height = height
        self.color = color
        self.top = top
        self.left = left
        self.anchor = anchor

    def process(self, img):
        new_img = Image.new('RGBA', (self.width, self.height), self.color)
        if self.anchor:
            self.top = int(abs(self.width - img.size[0]) * Anchor._ANCHOR_PTS[self.anchor][0])
            self.left = int(abs(self.height - img.size[1]) * Anchor._ANCHOR_PTS[self.anchor][1])
        new_img.paste(img, (self.top, self.left))
        return new_img


class AddBorder(object):
    """
    Add a border of specific color and size to an image.

    """
    def __init__(self, color, thickness):
        """
        :param color: Color to use for the border
        :param thickness: Thickness of the border which is either an int or a 4-tuple of ints.
        """
        self.color = color
        if isinstance(thickness, int):
            self.top = self.right = self.bottom = self.left = thickness
        else:
            self.top, self.right, self.bottom, self.left = thickness

    def process(self, img):
        new_width = img.size[0] + self.left + self.right
        new_height = img.size[1] + self.top + self.bottom
        return ResizeCanvas(new_width, new_height, self.color, self.top, self.left).process(img)


class Fit(object):
    """
    Resizes an image to fit within the specified dimensions.

    """

    def __init__(self, width=None, height=None, upscale=None, mat_color=None, anchor=Anchor.CENTER):
        """
        :param width: The maximum width of the desired image.
        :param height: The maximum height of the desired image.
        :param upscale: A boolean value specifying whether the image should
            be enlarged if its dimensions are smaller than the target
            dimensions.
        :param mat_color: If set, the target image size will be enforced and the
            specified color will be used as a background color to pad the image.

        """
        self.width = width
        self.height = height
        self.upscale = upscale
        self.mat_color = mat_color
        self.anchor = anchor

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
                img = BasicResize(new_dimensions[0],
                        new_dimensions[1]).process(img)
        if self.mat_color:
            img = ResizeCanvas(self.width, self.height, self.mat_color, anchor=self.anchor).process(img)
        return img


class SmartCrop(crop.SmartCrop):
    def __init__(self, *args, **kwargs):
        warnings.warn('The SmartCrop processor has been moved to'
                ' `imagekit.processors.crop.SmartCrop`, where it belongs.',
                DeprecationWarning)
        super(SmartCrop, self).__init__(*args, **kwargs)
