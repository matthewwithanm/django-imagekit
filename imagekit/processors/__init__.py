"""
Imagekit image processors.

A processor accepts an image, does some stuff, and returns the result.
Processors can do anything with the image you want, but their responsibilities
should be limited to image manipulations--they should be completely decoupled
from both the filesystem and the ORM.

"""
from imagekit.lib import Image, ImageColor, ImageEnhance
from imagekit.processors import resize


class ProcessorPipeline(list):
    """
    A :class:`list` of other processors. This class allows any object that
    knows how to deal with a single processor to deal with a list of them.
    For example::

        processed_image = ProcessorPipeline([ProcessorA(), ProcessorB()]).process(image)

    """
    def process(self, img):
        for proc in self:
            img = proc.process(img)
        return img


class Adjust(object):
    """
    Performs color, brightness, contrast, and sharpness enhancements on the
    image. See :mod:`PIL.ImageEnhance` for more imformation.

    """
    def __init__(self, color=1.0, brightness=1.0, contrast=1.0, sharpness=1.0):
        """
        :param color: A number between 0 and 1 that specifies the saturation
            of the image. 0 corresponds to a completely desaturated image
            (black and white) and 1 to the original color.
            See :class:`PIL.ImageEnhance.Color`
        :param brightness: A number representing the brightness; 0 results in
            a completely black image whereas 1 corresponds to the brightness
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
    """
    Creates an image with a reflection.

    """
    background_color = '#FFFFFF'
    size = 0.0
    opacity = 0.6

    def process(self, img):
        # Convert bgcolor string to RGB value.
        background_color = ImageColor.getrgb(self.background_color)
        # Handle palleted images.
        img = img.convert('RGB')
        # Copy orignial image and flip the orientation.
        reflection = img.copy().transpose(Image.FLIP_TOP_BOTTOM)
        # Create a new image filled with the bgcolor the same size.
        background = Image.new("RGB", img.size, background_color)
        # Calculate our alpha mask.
        start = int(255 - (255 * self.opacity))  # The start of our gradient.
        steps = int(255 * self.size)  # The number of intermedite values.
        increment = (255 - start) / float(steps)
        mask = Image.new('L', (1, 255))
        for y in range(255):
            if y < steps:
                val = int(y * increment + start)
            else:
                val = 255
            mask.putpixel((0, y), val)
        alpha_mask = mask.resize(img.size)
        # Merge the reflection onto our background color using the alpha mask.
        reflection = Image.composite(background, reflection, alpha_mask)
        # Crop the reflection.
        reflection_height = int(img.size[1] * self.size)
        reflection = reflection.crop((0, 0, img.size[0], reflection_height))
        # Create new image sized to hold both the original image and
        # the reflection.
        composite = Image.new("RGB", (img.size[0], img.size[1] + reflection_height), background_color)
        # Paste the orignal image and the reflection into the composite image.
        composite.paste(img, (0, 0))
        composite.paste(reflection, (0, img.size[1]))
        # Return the image complete with reflection effect.
        return composite


class Transpose(object):
    """
    Rotates or flips the image.

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

        The order of the arguments dictates the order in which the
        Transposition steps are taken.

        If Transpose.AUTO is present, all other arguments are ignored, and
        the processor will attempt to rotate the image according to the
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
