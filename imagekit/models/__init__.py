from .fields import ImageSpecField, ProcessedImageField
import warnings


class ImageSpec(ImageSpecField):
    def __init__(self, *args, **kwargs):
        warnings.warn('ImageSpec has been moved to'
                ' imagekit.models.fields.ImageSpecField. Please use that'
                ' instead.', DeprecationWarning)
        super(ImageSpec, self).__init__(*args, **kwargs)
