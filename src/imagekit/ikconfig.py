from imagekit import specs


class ResizeThumbnail(specs.Resize):
    width = 100
    height = 75
    crop = True
    
class EnhanceSmall(specs.Adjustment):
    contrast = 1.2
    sharpness = 1.1
    
class Thumbnail(specs.Spec):
    processors = [ResizeThumbnail, EnhanceSmall]
