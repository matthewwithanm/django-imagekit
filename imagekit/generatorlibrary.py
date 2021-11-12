from .processors import Thumbnail as ThumbnailProcessor
from .registry import register
from .specs import ImageSpec


class Thumbnail(ImageSpec):
    def __init__(self, width=None, height=None, anchor=None, crop=None, upscale=None, **kwargs):
        self.processors = [ThumbnailProcessor(width, height, anchor=anchor,
                                              crop=crop, upscale=upscale)]
        super().__init__(**kwargs)


register.generator('imagekit:thumbnail', Thumbnail)
