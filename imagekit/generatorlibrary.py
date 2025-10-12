from .processors import Thumbnail as ThumbnailProcessor
from .registry import register
from .specs import ImageSpec
from django.conf import settings

default_thumbnail_format = getattr(settings, 'IMAGEKIT_DEFAULT_THUMBNAIL_FORMAT', None)

class Thumbnail(ImageSpec):
    def __init__(self, width=None, height=None, anchor=None, crop=None, upscale=None, format=default_thumbnail_format, **kwargs):
        self.processors = [ThumbnailProcessor(width, height, anchor=anchor,
                                              crop=crop, upscale=upscale)]
        super().__init__(**kwargs)
        self.format = format


register.generator('imagekit:thumbnail', Thumbnail)
