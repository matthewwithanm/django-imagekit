from imagekit.specs import ImageSpec
from imagekit import processors


class ResizeThumbnail(processors.Resize):
    width = 100
    height = 75
    crop = True
    
class EnhanceSmall(processors.Adjustment):
    contrast = 1.2
    sharpness = 1.1
    
class Thumbnail(ImageSpec):
    processors = [ResizeThumbnail, EnhanceSmall]
