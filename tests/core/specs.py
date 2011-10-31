from imagekit import processors
from imagekit.specs import ImageSpec


class ResizeToWidth(processors.Resize):
    width = 100


class ResizeToHeight(processors.Resize):
    height = 100


class ResizeToFit(processors.Resize):
    width = 100
    height = 100


class ResizeCropped(ResizeToFit):
    crop = ('center', 'center')


class TestResizeToWidth(ImageSpec):
    access_as = 'to_width'
    processors = [ResizeToWidth]


class TestResizeToHeight(ImageSpec):
    access_as = 'to_height'
    processors = [ResizeToHeight]


class TestResizeCropped(ImageSpec):
    access_as = 'cropped'
    processors = [ResizeCropped]
