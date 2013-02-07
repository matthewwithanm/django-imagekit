from .base import Anchor  # noqa
from .utils import histogram_entropy
from ..lib import Image, ImageChops, ImageDraw, ImageStat


class Side(object):
    TOP = 't'
    RIGHT = 'r'
    BOTTOM = 'b'
    LEFT = 'l'
    ALL = (TOP, RIGHT, BOTTOM, LEFT)


def _crop(img, bbox, sides=Side.ALL):
    bbox = (
        bbox[0] if Side.LEFT in sides else 0,
        bbox[1] if Side.TOP in sides else 0,
        bbox[2] if Side.RIGHT in sides else img.size[0],
        bbox[3] if Side.BOTTOM in sides else img.size[1],
    )
    return img.crop(bbox)


def detect_border_color(img):
    mask = Image.new('1', img.size, 1)
    w, h = img.size[0] - 2, img.size[1] - 2
    if w > 0 and h > 0:
        draw = ImageDraw.Draw(mask)
        draw.rectangle([1, 1, w, h], 0)
    return ImageStat.Stat(img.convert('RGBA').histogram(mask)).median


class TrimBorderColor(object):
    """Trims a color from the sides of an image.

    """
    def __init__(self, color=None, tolerance=0.3, sides=Side.ALL):
        """
        :param color: The color to trim from the image, in a 4-tuple RGBA value,
            where each component is an integer between 0 and 255, inclusive. If
            no color is provided, the processor will attempt to detect the
            border color automatically.
        :param tolerance: A number between 0 and 1 where 0. Zero is the least
            tolerant and one is the most.
        :param sides: A list of sides that should be trimmed. Possible values
            are provided by the :class:`Side` enum class.

        """
        self.color = color
        self.sides = sides
        self.tolerance = tolerance

    def process(self, img):
        source = img.convert('RGBA')
        border_color = self.color or tuple(detect_border_color(source))
        bg = Image.new('RGBA', img.size, border_color)
        diff = ImageChops.difference(source, bg)
        if self.tolerance not in (0, 1):
            # If tolerance is zero, we've already done the job. A tolerance of
            # one would mean to trim EVERY color, and since that would result
            # in a zero-sized image, we just ignore it.
            if not 0 <= self.tolerance <= 1:
                raise ValueError('%s is an invalid tolerance. Acceptable values'
                        ' are between 0 and 1 (inclusive).' % self.tolerance)
            tmp = ImageChops.constant(diff, int(self.tolerance * 255)) \
                    .convert('RGBA')
            diff = ImageChops.subtract(diff, tmp)

        bbox = diff.getbbox()
        if bbox:
            img = _crop(img, bbox, self.sides)
        return img


class Crop(object):
    """
    Crops an image, cropping it to the specified width and height. You may
    optionally provide either an anchor or x and y coordinates. This processor
    functions exactly the same as ``ResizeCanvas`` except that it will never
    enlarge the image.

    """

    def __init__(self, width=None, height=None, anchor=None, x=None, y=None):
        self.width = width
        self.height = height
        self.anchor = anchor
        self.x = x
        self.y = y

    def process(self, img):
        from .resize import ResizeCanvas

        original_width, original_height = img.size
        new_width, new_height = min(original_width, self.width), \
                min(original_height, self.height)

        return ResizeCanvas(new_width, new_height, anchor=self.anchor,
                x=self.x, y=self.y).process(img)


class SmartCrop(object):
    """
    Crop an image to the specified dimensions, whittling away the parts of the
    image with the least entropy.

    Based on smart crop implementation from easy-thumbnails:
        https://github.com/SmileyChris/easy-thumbnails/blob/master/easy_thumbnails/processors.py#L193

    """

    def __init__(self, width=None, height=None):
        """
        :param width: The target width, in pixels.
        :param height: The target height, in pixels.

        """
        self.width = width
        self.height = height

    def compare_entropy(self, start_slice, end_slice, slice, difference):
        """
        Calculate the entropy of two slices (from the start and end of an axis),
        returning a tuple containing the amount that should be added to the start
        and removed from the end of the axis.

        """
        start_entropy = histogram_entropy(start_slice)
        end_entropy = histogram_entropy(end_slice)

        if end_entropy and abs(start_entropy / end_entropy - 1) < 0.01:
            # Less than 1% difference, remove from both sides.
            if difference >= slice * 2:
                return slice, slice
            half_slice = slice // 2
            return half_slice, slice - half_slice

        if start_entropy > end_entropy:
            return 0, slice
        else:
            return slice, 0

    def process(self, img):
        source_x, source_y = img.size
        diff_x = int(source_x - min(source_x, self.width))
        diff_y = int(source_y - min(source_y, self.height))
        left = top = 0
        right, bottom = source_x, source_y

        while diff_x:
            slice = min(diff_x, max(diff_x // 5, 10))
            start = img.crop((left, 0, left + slice, source_y))
            end = img.crop((right - slice, 0, right, source_y))
            add, remove = self.compare_entropy(start, end, slice, diff_x)
            left += add
            right -= remove
            diff_x = diff_x - add - remove

        while diff_y:
            slice = min(diff_y, max(diff_y // 5, 10))
            start = img.crop((0, top, source_x, top + slice))
            end = img.crop((0, bottom - slice, source_x, bottom))
            add, remove = self.compare_entropy(start, end, slice, diff_y)
            top += add
            bottom -= remove
            diff_y = diff_y - add - remove

        box = (left, top, right, bottom)
        img = img.crop(box)
        return img
