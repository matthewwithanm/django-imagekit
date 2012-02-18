from imagekit.lib import Image, ImageColor, ImageEnhance


RGBA_TRANSPARENCY_FORMATS = ['PNG']
PALETTE_TRANSPARENCY_FORMATS = ['PNG', 'GIF']


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
        original = img = img.convert('RGBA')
        for name in ['Color', 'Brightness', 'Contrast', 'Sharpness']:
            factor = getattr(self, name.lower())
            if factor != 1.0:
                try:
                    img = getattr(ImageEnhance, name)(img).enhance(factor)
                except ValueError:
                    pass
                else:
                    # PIL's Color and Contrast filters both convert the image
                    # to L mode, losing transparency info, so we put it back.
                    # See https://github.com/jdriscoll/django-imagekit/issues/64
                    if name in ('Color', 'Contrast'):
                        img = Image.merge('RGBA', img.split()[:3] +
                                original.split()[3:4])
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
            except (KeyError, TypeError, AttributeError):
                ops = []
        else:
            ops = self.methods
        for method in ops:
            img = img.transpose(method)
        return img


class AutoConvert(object):
    """A processor that does some common-sense conversions based on the target
    format. This includes things like preserving transparency and quantizing.
    This processors is used automatically by ``ImageSpecField`` and
    ``ProcessedImageField`` immediately before saving the image unless you
    specify ``autoconvert=False``.

    """

    def __init__(self, format):
        self.format = format

    def process(self, img):
        matte = False
        self.save_kwargs = {}
        self.rgba_ = img.mode == 'RGBA'
        if self.rgba_:
            if self.format in RGBA_TRANSPARENCY_FORMATS:
                pass
            elif self.format in PALETTE_TRANSPARENCY_FORMATS:
                # If you're going from a format with alpha transparency to one
                # with palette transparency, transparency values will be
                # snapped: pixels that are more opaque than not will become
                # fully opaque; pixels that are more transparent than not will
                # become fully transparent. This will not produce a good-looking
                # result if your image contains varying levels of opacity; in
                # that case, you'll probably want to use a processor to matte
                # the image on a solid color. The reason we don't matte by
                # default is because not doing so allows processors to treat
                # RGBA-format images as a super-type of P-format images: if you
                # have an RGBA-format image with only a single transparent
                # color, and save it as a GIF, it will retain its transparency.
                # In other words, a P-format image converted to an
                # RGBA-formatted image by a processor and then saved as a
                # P-format image will give the expected results.
                alpha = img.split()[-1]
                mask = Image.eval(alpha, lambda a: 255 if a <= 128 else 0)
                img = img.convert('RGB').convert('P', palette=Image.ADAPTIVE,
                        colors=255)
                img.paste(255, mask)
                self.save_kwargs['transparency'] = 255
            else:
                # Simply converting an RGBA-format image to an RGB one creates a
                # gross result, so we matte the image on a white background. If
                # that's not what you want, that's fine: use a processor to deal
                # with the transparency however you want. This is simply a
                # sensible default that will always produce something that looks
                # good. Or at least, it will look better than just a straight
                # conversion.
                matte = True
        elif img.mode == 'P':
            if self.format in PALETTE_TRANSPARENCY_FORMATS:
                try:
                    self.save_kwargs['transparency'] = img.info['transparency']
                except KeyError:
                    pass
            elif self.format in RGBA_TRANSPARENCY_FORMATS:
                # Currently PIL doesn't support any RGBA-mode formats that
                # aren't also P-mode formats, so this will never happen.
                img = img.convert('RGBA')
            else:
                matte = True
        else:
            img = img.convert('RGB')

            # GIFs are always going to be in palette mode, so we can do a little
            # optimization. Note that the RGBA sources also use adaptive
            # quantization (above). Images that are already in P mode don't need
            # any quantization because their colors are already limited.
            if self.format == 'GIF':
                img = img.convert('P', palette=Image.ADAPTIVE)

        if matte:
            img = img.convert('RGBA')
            bg = Image.new('RGBA', img.size, (255, 255, 255))
            bg.paste(img, img)
            img = bg.convert('RGB')

        if self.format == 'JPEG':
            self.save_kwargs['optimize'] = True

        return img


class Anchor(object):
    """
    Defines all the anchor points needed by the various processor classes.

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

    @staticmethod
    def get_tuple(anchor):
        """Normalizes anchor values (strings or tuples) to tuples.

        """
        # If the user passed in one of the string values, convert it to a
        # percentage tuple.
        if anchor in Anchor._ANCHOR_PTS.keys():
            anchor = Anchor._ANCHOR_PTS[anchor]
        return anchor
