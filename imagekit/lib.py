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
