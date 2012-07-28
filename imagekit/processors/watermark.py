# -*- coding: utf-8 -*-
#
# watermark processors for django-imagekit
# some inspiration from http://code.activestate.com/recipes/362879-watermark-with-pil/
#

from abc import abstractmethod, ABCMeta
from imagekit.lib import Image
from imagekit.lib import ImageDraw, ImageFont, ImageColor, ImageEnhance
import warnings
import weakref

__all__ = ('ImageWatermark', 'TextWatermark', 'ReverseWatermark')


def _process_coords(img_size, wm_size, coord_spec):
    """
    Given the dimensions of the image and the watermark as (x,y) tuples and a
    location specification, return the coordinates where the watermark should
    be placed according to the specification in a (x,y) tuple.

    Specification can use pixels, percentage (provided as a string, such as
    "30%"), or keywords such as top, bottom, center, left and right.
    """
    (sh, sv) = coord_spec
    if sh in ('top','bottom') or sv in ('left','right'):
        # coords were written in wrong order, but there's an easy fix
        (sv, sh) = coord_spec

    if isinstance(sh, basestring) and '%' in sh:
        sh = int(img_size[0] * float(sh.rstrip("%")) / 100)

    if isinstance(sh, int) and sh < 0:
        sh = img_size[0] - wm_size[0] + sh

    if sh == 'left':
        sh = 0
    elif sh == 'center':
        sh = (img_size[0] - wm_size[0]) / 2
    elif sh == 'right':
        sh = img_size[0] - wm_size[0]

    
    if isinstance(sv, basestring) and '%' in sv:
        sv = int(img_size[1] * float(sv.rstrip("%")) / 100)

    if isinstance(sv, int) and sv < 0:
        sv = img_size[1] - wm_size[1] + sv

    if sv == 'top':
        sv = 0
    elif sv == 'center':
        sv = (img_size[1] - wm_size[1]) / 2
    elif sv == 'bottom':
        sv = img_size[1] - wm_size[1]

    return (sh, sv)


class AbstractWatermark(object):
    """
    Base class for ``ImageWatermark`` and ``TextWatermark``.

    Some properties that are used in processors based on this class are:

    ``opacity`` may be specified as a float ranging from 0.0 to 1.0.

    ``position`` is a tuple containing coordinates for horizontal and
    vertical axis. Instead of coordinates you may use strings such as "left",
    "center", "right", "top" or "bottom". You may also specify percentage
    values such as "70%". Negative values will count from the opposite
    margin. As such, `('66%', 'bottom')` and `('-33%', 'bottom')` are
    equivalent.

    ``scale`` can be a numeric scale factor or ``True``, in which case the
    watermark will be scaled to fit the base image, using the mechanics from
    ``ResizeToFit``.

    ``repeat`` specifies if the watermark should be repeated throughout the
    base image. The repeat pattern will be influenced by both ``scale`` and
    ``position``.

    ``cache_mark`` specifies if the watermark layer that is merged into the
    images should be cached rather than calculated every time a processing
    runs, allowing a trade of CPU time for memory usage *(this option is
    currently not implemented)*.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def get_watermark(self):
        return

    def _get_watermark(self):
        if not self.cache_mark:
            return self.get_watermark()
        else:
            # cache watermark and use it
            if self.cache_get_wm is None:
                wm = None
            else:
                wm = self.cache_get_wm()

            if wm is None:
                wm = self.get_watermark()
                self.cache_get_wm = weakref.ref(wm)
                return wm



    def _fill_options(self, opacity=1.0, position=('center','center'),
            repeat=False, scale=None, cache_mark=True):
        """Store common properties"""

        self.opacity = opacity
        self.position = position
        self.repeat = repeat
        self.scale = scale
        self.cache_mark = cache_mark
        if cache_mark:
            self.cache_get_wm = None

    def process(self, img):

        # get watermark
        wm = self._get_watermark()
        wm_size = wm.size

        if self.scale:
            if isinstance(self.scale, (int, float)) and self.scale != 1:
                wm_size[0] *= self.scale
                wm_size[1] *= self.scale
                wm = wm.scale(wm_size)
            elif self.scale == True:
                from .resize import ResizeToFit
                wm = ResizeToFit(width=img.size[0], height=img.size[1],
                        upscale=True).process(wm)
                wm_size = wm.size


        # prepare image for overlaying (ensure alpha channel)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # create a layer to place the watermark
        layer = Image.new('RGBA', img.size, (0,0,0,0))
        coords = _process_coords(img.size, wm_size, self.position)

        if self.repeat:
            sx = coords[0] % wm_size[0] - wm_size[0]
            sy = coords[1] % wm_size[1] - wm_size[1]
            for x in range(sx, img.size[0], wm_size[0]):
                for y in range(sy, img.size[1], wm_size[1]):
                    layer.paste(wm, (x,y))
        else:
            layer.paste(wm, coords)


        if self.opacity < 1:
            alpha = layer.split()[3]
            alpha = ImageEnhance.Brightness(alpha).enhance(self.opacity)
            layer.putalpha(alpha)

        # merge watermark layer
        img = Image.composite(layer, img, layer)

        return img


class ImageWatermark(AbstractWatermark):
    """
    Creates a watermark using an image.

    ``watermark`` is the path to the image to be overlaid on the processed
    image, or a storage (File-like) object that allows accessing the image.
    """

    def get_watermark(self):
        # open the image despite the format that the user provided for it
        if self.watermark:
            return self.watermark
        if self.watermark_image:
            return self.watermark_image

        if self.watermark_file:
            return Image.open(self.watermark_file)
        if self.watermark_path:
            return Image.open(self.watermark_path)

    def __init__(self, watermark, **kwargs):
        # fill in base defaults
        defaults = dict(opacity=1.0)
        defaults.update(kwargs)
        self._fill_options(**defaults)

        # fill in specific settings
        self.watermark = None
        self.watermark_image = self.watermark_file = self.watermark_path = None

        # we accept PIL Image objects, file-like objects or file paths 
        if isinstance(watermark, Image.Image):
            self.watermark_image = watermark
        elif hasattr(watermark, "read") and callable(watermark.open):
            self.watermark_file = watermark
        elif isinstance(watermark, basestring):
            self.watermark_path = watermark
        else:
            raise TypeError("watermark must be a PIL Image, file-like object or "
                    "a path")


class ReverseWatermark(ImageWatermark):
    """
    Same as ImageWatermark but instead of putting the watermark in the image
    being processed, puts the image being processed on the watermark.
    """

    def __init__(self, *args, **kwargs):
        super(ReverseWatermark, self).__init__(*args, **kwargs)

    def get_watermark(self):
        return self._img

    def process(self, img):
        # we invoke the base process() method, but before we do,
        # we switch get_watermark() and the `img` argument
        self._img = img
        watermark = super(ReverseWatermark, self).get_watermark()
        final = super(ReverseWatermark, self).process(watermark)
        del self._img
        return final


class TextWatermark(AbstractWatermark):
    """
    Adds a watermark to the image with the specified text.

    You may adjust the font, color and position.

    ``text_color`` may be a string in a format supported by PIL's
    ``ImageColor``, as described in the handbook [1] or a tuple containing
    values in the 0-255 range for (R, G, B).

    ``font`` can be specified as a path to a `TrueType` font or a tuple in
    the form of (path, size).

    For details on ``scale``, ``position`` and ``repeat``, check the
    documentation on ``AbstractWatermark``.

    [1]: http://www.pythonware.com/library/pil/handbook/imagecolor.htm
    """

    def __init__(self, text, font=None, text_color=None, **kwargs):
        # fill in base defaults
        defaults = dict(opacity=0.5)
        defaults.update(kwargs)
        self._fill_options(**defaults)

        # fill in specific settings
        self.text = text

        if isinstance(font, basestring):
            # `font` is a path to a font
            fontpath = font
            fontsize = 16

        elif isinstance(font, tuple):
            # `font` is a (path, size) tuple
            fontpath = font[0]
            fontsize = font[1]

        elif font is not None:
            raise TypeError("Expected 'font' to be a path to a font file "
                    "or a tuple containing (path, size).")

        try:
            if fontpath.endswith(".pil"):
                # bitmap font (size doesn't matter)
                self.font = ImageFont.load(fontpath)
            else:
                # truetype font (size matters)
                self.font = ImageFont.truetype(fontpath, fontsize)
        except:
            warnings.warn("The specified font '%s' could not be loaded" %
                    (font,), RuntimeWarning)
            font = None

        if not font:
            self.font = ImageFont.load_default()

        if text_color is None:
            # fallback to default
            self.text_color = (255,255,255)
        elif isinstance(text_color, basestring):
            # string in a form ImageColor module can process
            self.text_color = ImageColor.getrgb(text_color)
        elif isinstance(text_color, tuple):
            # tuple with (R,G,B)
            # if it has (R,G,B,A), the alpha component seems to be ignored by PIL
            # when rendering text
            self.text_color = text_color
        else:
            raise TypeError("Expected `text_color` to be tuple or string.")

        self.font_size = self.font.getsize(text)


    def get_watermark(self):
        wm = Image.new("RGBA", self.font_size, (0,0,0,0))
        draw = ImageDraw.Draw(wm, "RGBA")
        draw.text((0,0), self.text, font=self.font,
                fill=self.text_color)
        return wm

