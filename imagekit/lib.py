# flake8: noqa

# Required PIL classes may or may not be available from the root namespace
# depending on the installation method used.
try:
    from PIL import Image, ImageColor, ImageChops, ImageEnhance, ImageFile, \
            ImageFilter, ImageDraw, ImageStat
except ImportError:
    try:
        import Image
        import ImageColor
        import ImageChops
        import ImageEnhance
        import ImageFile
        import ImageFilter
        import ImageDraw
        import ImageStat
    except ImportError:
        raise ImportError('ImageKit was unable to import the Python Imaging Library. Please confirm it`s installed and available on your current Python path.')

try:
    from io import BytesIO as StringIO
except:
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO

try:
    from logging import NullHandler
except ImportError:
    from logging import Handler

    class NullHandler(Handler):
        def emit(self, record):
            pass

# Try to import `force_text` available from Django 1.5
# This function will replace `unicode` used in the code
# If Django version is under 1.5 then use `force_unicde`
# It is used for compatibility between Python 2 and Python 3
try:
    from django.utils.encoding import force_text, force_bytes, smart_text
except ImportError:
    # Django < 1.5
    from django.utils.encoding import (force_unicode as force_text,
                                       smart_str as force_bytes,
                                       smart_unicode as smart_text)

__all__ = ['Image', 'ImageColor', 'ImageChops', 'ImageEnhance', 'ImageFile',
           'ImageFilter', 'ImageDraw', 'ImageStat', 'StringIO', 'NullHandler',
           'force_text', 'force_bytes', 'smart_text']
