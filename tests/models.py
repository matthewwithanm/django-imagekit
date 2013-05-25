from django.db import models

from imagekit.models import ProcessedImageField
from imagekit.models import ImageSpecField
from imagekit.processors import Adjust, ResizeToFill, SmartCrop


class ImageModel(models.Model):
    image = models.ImageField(upload_to='b')


class Photo(models.Model):
    original_image = models.ImageField(upload_to='photos')

    # Implicit source field
    thumbnail = ImageSpecField([Adjust(contrast=1.2, sharpness=1.1),
                               ResizeToFill(50, 50)], format='JPEG',
                               options={'quality': 90})

    smartcropped_thumbnail = ImageSpecField([Adjust(contrast=1.2,
            sharpness=1.1), SmartCrop(50, 50)], source='original_image',
            format='JPEG', options={'quality': 90})


class ProcessedImageFieldModel(models.Model):
    processed = ProcessedImageField([SmartCrop(50, 50)], format='JPEG',
            options={'quality': 90}, upload_to='p')


class CountingCacheFileStrategy(object):
    def __init__(self):
        self.on_existence_required_count = 0
        self.on_content_required_count = 0
        self.on_source_saved_count = 0

    def on_existence_required(self, file):
        self.on_existence_required_count += 1

    def on_content_required(self, file):
        self.on_content_required_count += 1

    def on_source_saved(self, file):
        self.on_source_saved_count += 1


class AbstractImageModel(models.Model):
    original_image = models.ImageField(upload_to='photos')
    abstract_class_spec = ImageSpecField(source='original_image',
                                         format='JPEG',
                                         cachefile_strategy=CountingCacheFileStrategy())

    class Meta:
        abstract = True


class ConcreteImageModel(AbstractImageModel):
    pass


class ConcreteImageModelSubclass(ConcreteImageModel):
    pass
