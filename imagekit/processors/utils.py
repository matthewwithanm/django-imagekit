import math
from imagekit.lib import Image


def histogram_entropy(im):
    """
    Calculate the entropy of an images' histogram. Used for "smart cropping" in easy-thumbnails;
    see: https://raw.github.com/SmileyChris/easy-thumbnails/master/easy_thumbnails/utils.py

    """
    if not isinstance(im, Image.Image):
        return 0  # Fall back to a constant entropy.

    histogram = im.histogram()
    hist_ceil = float(sum(histogram))
    histonorm = [histocol / hist_ceil for histocol in histogram]

    return -sum([p * math.log(p, 2) for p in histonorm if p != 0])
