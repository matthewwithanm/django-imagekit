
import math
from imagekit.lib import Image


class Crop(object):
    """
    Resizes an image , cropping it to the specified width and height.

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
        self.width = width
        self.height = height
        self.anchor = anchor

    def process(self, img):
        cur_width, cur_height = img.size
        horizontal_anchor, vertical_anchor = Crop._ANCHOR_PTS[self.anchor or \
                Crop.CENTER]
        ratio = max(float(self.width) / cur_width, float(self.height) / cur_height)
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


class Fit(object):
    """
    Resizes an image to fit within the specified dimensions.

    """
    def __init__(self, width=None, height=None, upscale=None):
        """
        :param width: The maximum width of the desired image.
        :param height: The maximum height of the desired image.
        :param upscale: A boolean value specifying whether the image should
            be enlarged if its dimensions are smaller than the target
            dimensions.

        """
        self.width = width
        self.height = height
        self.upscale = upscale

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
        if new_dimensions[0] > cur_width or \
           new_dimensions[1] > cur_height:
            if not self.upscale:
                return img
        img = img.resize(new_dimensions, Image.ANTIALIAS)
        return img


def histogram_entropy(im):
    """
    Calculate the entropy of an images' histogram. Used for "smart cropping" in easy-thumbnails;
    see: https://raw.github.com/SmileyChris/easy-thumbnails/master/easy_thumbnails/utils.py
    
    """
    if not isinstance(im, Image.Image):
        return 0 # Fall back to a constant entropy.
    
    histogram = im.histogram()
    hist_ceil = float(sum(histogram))
    histonorm = [histocol / hist_ceil for histocol in histogram]
    
    return -sum([p * math.log(p, 2) for p in histonorm if p != 0])


class SmartCrop(object):
    """
    Crop an image 'smartly' -- based on smart crop implementation from easy-thumbnails:
    
        https://github.com/SmileyChris/easy-thumbnails/blob/master/easy_thumbnails/processors.py#L193
    
    Smart cropping whittles away the parts of the image with the least entropy.
    
    """
    
    def __init__(self, width=None, height=None):
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

