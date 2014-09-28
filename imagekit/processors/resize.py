import warnings

from pilkit.processors.resize import *

warnings.warn('imagekit.processors.resize is deprecated use imagekit.processors instead', DeprecationWarning)

__all__ = ['Resize', 'ResizeToCover', 'ResizeToFill', 'SmartResize', 'ResizeCanvas', 'AddBorder', 'ResizeToFit', 'Thumbnail']
