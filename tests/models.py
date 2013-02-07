from django.db import models

from imagekit.models import ProcessedImageField
from imagekit.models import ImageSpecField
from imagekit.processors import Adjust, ResizeToFill, SmartCrop


class ImageModel(models.Model):
    image = models.ImageField(upload_to='b')


class Photo(models.Model):
    original_image = models.ImageField(upload_to='photos')

    thumbnail = ImageSpecField([Adjust(contrast=1.2, sharpness=1.1),
            ResizeToFill(50, 50)], source='original_image', format='JPEG',
            options={'quality': 90})

    smartcropped_thumbnail = ImageSpecField([Adjust(contrast=1.2,
            sharpness=1.1), SmartCrop(50, 50)], source='original_image',
            format='JPEG', options={'quality': 90})


class ProcessedImageFieldModel(models.Model):
    processed = ProcessedImageField([SmartCrop(50, 50)], format='JPEG',
            options={'quality': 90}, upload_to='p')


class AbstractImageModel(models.Model):
    original_image = models.ImageField(upload_to='photos')
    abstract_class_spec = ImageSpecField()

    class Meta:
        abstract = True


class ConcreteImageModel1(AbstractImageModel):
    first_spec = ImageSpecField()


class ConcreteImageModel2(AbstractImageModel):
    second_spec = ImageSpecField()
