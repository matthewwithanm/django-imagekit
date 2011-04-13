""" Imagekit Image "ImageProcessors"

A processor defines a set of class variables (optional) and a
class method named "process" which processes the supplied image using
the class properties as settings. The process method can be overridden as well allowing user to define their
own effects/processes entirely.

"""
import os
from imagekit.lib import *
from imagekit.utils import md5_for_file

class ImageProcessor(object):
    """ Base image processor class """

    @classmethod
    def process(cls, img, fmt, obj):
        return img, fmt


class Adjustment(ImageProcessor):
    color = 1.0
    brightness = 1.0
    contrast = 1.0
    sharpness = 1.0

    @classmethod
    def process(cls, img, fmt, obj):
        img = img.convert('RGB')
        for name in ['Color', 'Brightness', 'Contrast', 'Sharpness']:
            factor = getattr(cls, name.lower())
            if factor != 1.0:
                try:
                    img = getattr(ImageEnhance, name)(img).enhance(factor)
                except ValueError:
                    pass
        return img, fmt

"""
ICCProofTransform and ICCTransform should both get refactored -- probably, they should
inherit from a common abstract ancestor that implements process() in a non-stupid way.
"""

class ICCTransform(ImageProcessor):
    """
    Convert the image to a destination profile via the L*a*b colorspace.
    
    Source image numbers are treated as per its embedded profile by default;
    this may be (losslessly) overridden by an applied profile at conversion time.
    Untagged RGB images are treated as sRGB IEC61966-2.1 by default.
    I will figure out a default for CMYK and other spaces when I find myself
    inundated with enough files to pick something sensible.
    
    Relative colorimetric is the default intent.
    """
    _srgb = os.path.join(IK_ROOT, "icc/sRGB-IEC61966-2-1.icc")
    _srgb_profile = ImageCms.ImageCmsProfile(_srgb)
    source = None
    destination = None
    destination_profile = None
    
    mode = 'RGB' # for now
    intent = ImageCms.INTENT_RELATIVE_COLORIMETRIC
    transformers = {}
    
    @classmethod
    def process(cls, img, fmt, obj):
        if not img.mode == "L":
            
            iccpth = obj._iccpath
            if not iccpth:
                iccpth = cls.source
            if not iccpth:
                iccpth = cls._srgb
            
            if obj._icc_filehash:
                if obj._icc_filehash not in cls.transformers:
                    if not os.path.exists(cls.destination):
                        raise AttributeError("WTF: destination transform ICC profile %s doesn't exist" % cls.destination)
                    
                    source_profile = ImageCms.ImageCmsProfile(iccpth)
                    if not cls.destination_profile:
                        cls.destination_profile = ImageCms.ImageCmsProfile(cls.destination)
                    
                    cls.transformers[obj._icc_filehash] = ImageCms.ImageCmsTransform(
                        source_profile,
                        cls.destination_profile,
                        img.mode,
                        cls.mode,
                        cls.intent,
                    )
                
                return cls.transformers[obj._icc_filehash].apply(img), img.format
            
        return ImageCms.profileToProfile(
            img.convert('RGB'),
            cls._srgb_profile,
            cls.destination_profile and cls.destination_profile or cls._srgb_profile,
            cls.intent,
            cls.mode,
        ), img.format
    


class ICCProofTransform(ImageProcessor):
    """
    Convert the image to a destination profile via the L*a*b colorspace.
    
    Source image numbers are treated as per its embedded profile by default;
    this may be (losslessly) overridden by an applied profile at conversion time.
    Untagged RGB images are treated as sRGB IEC61966-2.1 by default.
    I will figure out a default for CMYK and other spaces when I find myself
    inundated with enough files to pick something sensible.
    
    Relative colorimetric is the default intent.
    """
    _srgb = os.path.join(IK_ROOT, "icc/sRGB-IEC61966-2-1.icc")
    _srgb_profile = ImageCms.ImageCmsProfile(_srgb)
    source = None
    destination = None
    destination_profile = None
    proof = None
    proof_profile = None
    
    mode = 'RGB' # for now
    intent = ImageCms.INTENT_RELATIVE_COLORIMETRIC
    proof_intent = ImageCms.INTENT_ABSOLUTE_COLORIMETRIC
    transformers = {}
    
    @classmethod
    def process(cls, img, fmt, obj):
        if not img.mode == "L":
            
            iccpth = obj._iccpath
            if not iccpth:
                iccpth = cls.source
            if not iccpth:
                iccpth = cls._srgb
            
            if obj._icc_filehash:
                if obj._icc_filehash not in cls.transformers:
                    if not os.path.exists(cls.destination):
                        raise AttributeError("WTF: destination transform ICC profile %s doesn't exist" % cls.destination)
                    if not os.path.exists(cls.proof):
                        raise AttributeError("WTF: proof transform ICC profile %s doesn't exist" % cls.proof)
                
                    source_profile = ImageCms.ImageCmsProfile(iccpth)
                    if not cls.destination_profile:
                        cls.destination_profile = ImageCms.ImageCmsProfile(cls.destination)
                    if not cls.proof_profile:
                        cls.proof_profile = ImageCms.ImageCmsProfile(cls.destination)
                
                    cls.transformers[obj._icc_filehash] = ImageCms.ImageCmsTransform(
                        source_profile,
                        cls.destination_profile,
                        img.mode,
                        cls.mode,
                        cls.intent,
                        proof=cls.proof_profile,
                        proof_intent=cls.proof_intent,
                    )
                
                return cls.transformers[obj._icc_filehash].apply(img), img.format
            
        return ImageCms.profileToProfile(
            img.convert('RGB'),
            cls._srgb_profile,
            cls.destination_profile and cls.destination_profile or cls._srgb_profile,
            cls.intent,
            cls.mode,
        ), img.format


class Format(ImageProcessor):
    format = 'JPEG'
    extension = 'jpg'

    @classmethod
    def process(cls, img, fmt, obj):
        return img, cls.format


class Reflection(ImageProcessor):
    background_color = '#FFFFFF'
    size = 0.0
    opacity = 0.6

    @classmethod
    def process(cls, img, fmt, obj):
        # convert bgcolor string to rgb value
        background_color = ImageColor.getrgb(cls.background_color)
        # handle palleted images
        img = img.convert('RGB')
        # copy orignial image and flip the orientation
        reflection = img.copy().transpose(Image.FLIP_TOP_BOTTOM)
        # create a new image filled with the bgcolor the same size
        background = Image.new("RGB", img.size, background_color)
        # calculate our alpha mask
        start = int(255 - (255 * cls.opacity)) # The start of our gradient
        steps = int(255 * cls.size) # the number of intermedite values
        increment = (255 - start) / float(steps)
        mask = Image.new('L', (1, 255))
        for y in range(255):
            if y < steps:
                val = int(y * increment + start)
            else:
                val = 255
            mask.putpixel((0, y), val)
        alpha_mask = mask.resize(img.size)
        # merge the reflection onto our background color using the alpha mask
        reflection = Image.composite(background, reflection, alpha_mask)
        # crop the reflection
        reflection_height = int(img.size[1] * cls.size)
        reflection = reflection.crop((0, 0, img.size[0], reflection_height))
        # create new image sized to hold both the original image and the reflection
        composite = Image.new("RGB", (img.size[0], img.size[1]+reflection_height), background_color)
        # paste the orignal image and the reflection into the composite image
        composite.paste(img, (0, 0))
        composite.paste(reflection, (0, img.size[1]))
        # Save the file as a JPEG
        fmt = 'JPEG'
        # return the image complete with reflection effect
        return composite, fmt


class Resize(ImageProcessor):
    width = None
    height = None
    crop = False
    upscale = False

    @classmethod
    def process(cls, img, fmt, obj):
        cur_width, cur_height = img.size
        if cls.crop:
            crop_horz = getattr(obj, obj._ik.crop_horz_field, 1)
            crop_vert = getattr(obj, obj._ik.crop_vert_field, 1)
            ratio = max(float(cls.width)/cur_width, float(cls.height)/cur_height)
            resize_x, resize_y = ((cur_width * ratio), (cur_height * ratio))
            crop_x, crop_y = (abs(cls.width - resize_x), abs(cls.height - resize_y))
            x_diff, y_diff = (int(crop_x / 2), int(crop_y / 2))
            box_left, box_right = {
                0: (0, cls.width),
                1: (int(x_diff), int(x_diff + cls.width)),
                2: (int(crop_x), int(resize_x)),
            }[crop_horz]
            box_upper, box_lower = {
                0: (0, cls.height),
                1: (int(y_diff), int(y_diff + cls.height)),
                2: (int(crop_y), int(resize_y)),
            }[crop_vert]
            box = (box_left, box_upper, box_right, box_lower)
            img = img.resize((int(resize_x), int(resize_y)), Image.ANTIALIAS).crop(box)
        else:
            if not cls.width is None and not cls.height is None:
                ratio = min(float(cls.width)/cur_width,
                            float(cls.height)/cur_height)
            else:
                if cls.width is None:
                    ratio = float(cls.height)/cur_height
                else:
                    ratio = float(cls.width)/cur_width
            new_dimensions = (int(round(cur_width*ratio)),
                              int(round(cur_height*ratio)))
            if new_dimensions[0] > cur_width or \
               new_dimensions[1] > cur_height:
                if not cls.upscale:
                    return img, fmt
            img = img.resize(new_dimensions, Image.ANTIALIAS)
        return img, fmt


class Transpose(ImageProcessor):
    """ Rotates or flips the image

    Method should be one of the following strings:
        - FLIP_LEFT RIGHT
        - FLIP_TOP_BOTTOM
        - ROTATE_90
        - ROTATE_270
        - ROTATE_180
        - auto

    If method is set to 'auto' the processor will attempt to rotate the image
    according to the EXIF Orientation data.

    """
    EXIF_ORIENTATION_STEPS = {
        1: [],
        2: ['FLIP_LEFT_RIGHT'],
        3: ['ROTATE_180'],
        4: ['FLIP_TOP_BOTTOM'],
        5: ['ROTATE_270', 'FLIP_LEFT_RIGHT'],
        6: ['ROTATE_270'],
        7: ['ROTATE_90', 'FLIP_LEFT_RIGHT'],
        8: ['ROTATE_90'],
    }

    method = 'auto'

    @classmethod
    def process(cls, img, fmt, obj):
        if cls.method == 'auto':
            try:
                orientation = Image.open(obj._imgfield.file)._getexif()[0x0112]
                ops = cls.EXIF_ORIENTATION_STEPS[orientation]
            except:
                ops = []
        else:
            ops = [cls.method]
        for method in ops:
            img = img.transpose(getattr(Image, method))
        return img, fmt
