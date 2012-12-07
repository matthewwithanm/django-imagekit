from .registry import register
from .processors import Thumbnail as ThumbnailProcessor
from .specs import ImageSpec


class Thumbnail(ImageSpec):
    def __init__(self, width=None, height=None, anchor='auto', crop=True, **kwargs):
        self.processors = [ThumbnailProcessor(width, height, anchor=anchor,
                                              crop=crop)]
        super(Thumbnail, self).__init__(**kwargs)


register.spec('ik:thumbnail', Thumbnail)
