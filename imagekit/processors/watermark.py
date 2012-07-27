# -*- coding: utf-8 -*-
from imagekit.lib import Image
#import warnings

from imagekit.lib import ImageDraw, ImageFont, ImageColor, ImageEnhance

def _process_coords(img_size, wm_size, coord_spec):
    """
    Given the dimensions of the image and the watermark as (x,y) tuples and a
    location specification, return the coordinates where the watermark should
    be placed according to the specification in a (x,y) tuple.

    Specification can use pixels, percentage (provided as a string, such as
    "30%"), or keywords such as top, bottom, center, left and right.
    """
    (sh, sv) = coord_spec

    if '%' in sh:
        sh = int(img_size[0] * float(sh.rstrip("%")) / 100)

    if isinstance(sh, int) and sh < 0:
        sh = img_size[0] - wm_size[0] + sh

    if sh == 'left':
        sh = 0
    elif sh == 'center':
        sh = (img_size[0] - wm_size[0]) / 2
    elif sh == 'right':
        sh = img_size[0] - wm_size[0]

    
    if '%' in sv:
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

class ImageWatermark(object):
    """
    Creates a watermark using an image
    """

    def get_watermark(self):
        if self.watermark:
            return self.watermark
        if self.watermark_image:
            return self.watermark_image

        if self.watermark_file:
            return Image.open(self.watermark_file)
        if self.watermark_path:
            return Image.open(self.watermark_path)

    def __init__(self, watermark, opacity=1.0, position=('center','center')):

        self.watermark = None
        self.watermark_image = self.watermark_file = self.watermark_path = None

        if isinstance(watermark, Image.Image):
            self.watermark_image = watermark
        elif hasattr(watermark, "open") and callable(watermark.open):
            self.watermark_file = watermark
        elif isinstance(watermark, basestring):
            self.watermark_path = watermark
        else:
            raise TypeError("watermark must be a PIL Image, file-like object or "
                    "a path")

        self.opacity = opacity
        self.position = position

    def process(self, img):

        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        layer = Image.new('RGBA', img.size, (0,0,0,0))
        wm = self.get_watermark()
        
        coords = _process_coords(img.size, wm.size, self.position)
        layer.paste(wm, coords)

        alpha = layer.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(self.opacity)
        layer.putalpha(alpha)

        img = Image.composite(layer, img, layer)

        return img

class TextWatermark(object):
    """
    Adds a watermark to the image with the specified text.

    You may also adjust the font, color and position.

    ``text_color`` may be a string in a format supported by PIL's
    ``ImageColor``, as described in the handbook [1] or a tuple containing
    values in the 0-255 range for (R, G, B).

    ``opacity`` may be specified as a float ranging from 0.0 to 1.0.

    ``position`` is a tuple containing coordinates for horizontal and
    vertical axis. Instead of coordinates you may use strings such as "left",
    "center", "right", "top" or "bottom". You may also specify percentage
    values such as "70%". Negative values will count from the opposite
    margin. As such, `('66%', 'bottom')` and `('-33%', 'bottom')` are
    equivalent.

    [1]: http://www.pythonware.com/library/pil/handbook/imagecolor.htm
    """

    def __init__(self, text, font=None, text_color=None, opacity=0.5,
            position=('center','center')):
        self.text = text
        self.font = (font or ImageFont.load_default())
        self.opacity = opacity

        if text_color is None:
            self.text_color = (255,255,255)
        elif isinstance(text_color, basestring):
            self.text_color = ImageColor.getrgb(text_color)
        elif isinstance(text_color, tuple):
            self.text_color = text_color
        else:
            raise TypeError("Expected `text_color` to be tuple or string.")

        self.font_size = self.font.getsize(text)
        self.position = position


    def process(self, img):

        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        layer = Image.new('RGBA', img.size, (0,0,0,0))
        draw = ImageDraw.Draw(layer, "RGBA")

        coords = _process_coords(img.size, self.font_size, self.position)
        draw.text( coords, self.text, font=self.font,
                fill=self.text_color)

        alpha = layer.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(self.opacity)
        layer.putalpha(alpha)

        img = Image.composite(layer, img, layer)
        return img
        

def testme2():
    bgo = Image.open("../outroolhar.png")
    bg = Image.open("../bg.png")
    iw = ImageWatermark("../outroolhar.png", opacity=0.5,
            position=('-66%', 'bottom'))
    iw.process(bg).save('../bg2.png')

def testme():
    bgo = Image.open("../outroolhar.png")
    bg = Image.open("../bg.png")
    tw = TextWatermark("awesome", text_color="black", opacity=0.5,
            font=ImageFont.truetype("/Library/Fonts/Arial Bold.ttf", 24),
            position=('-66%', 'bottom'))
    tw.process(bg).save('../bg2.png')
    
