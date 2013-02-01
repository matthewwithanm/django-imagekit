from imagekit import ImageSpec, register
from imagekit.processors import ResizeToFill


class TestSpec(ImageSpec):
    pass


class ResizeTo1PixelSquare(ImageSpec):
    def __init__(self, width=None, height=None, anchor=None, crop=None, **kwargs):
        self.processors = [ResizeToFill(1, 1)]
        super(ResizeTo1PixelSquare, self).__init__(**kwargs)


register.generator('testspec', TestSpec)
register.generator('1pxsq', ResizeTo1PixelSquare)
