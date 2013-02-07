from .registry import register
from .processors import Thumbnail as ThumbnailProcessor
from .specs import ImageSpec


class Thumbnail(ImageSpec):
    def __init__(self, width=None, height=None, anchor=None, crop=None, **kwargs):
        self.processors = [ThumbnailProcessor(width, height, anchor=anchor,
                                              crop=crop)]
        super(Thumbnail, self).__init__(**kwargs)


register.generator('imagekit:thumbnail', Thumbnail)
