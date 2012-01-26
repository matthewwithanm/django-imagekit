from ..lib import Image, ImageChops, ImageDraw, ImageStat


class Side(object):
    TOP = 't'
    RIGHT = 'r'
    BOTTOM = 'b'
    LEFT = 'l'
    ALL = (TOP, RIGHT, BOTTOM, LEFT)


def crop(img, bbox, sides=Side.ALL):
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
            img = crop(img, bbox, self.sides)

        return img
