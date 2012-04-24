from django.db import models

from imagekit.models import ImageSpecField
from imagekit.processors import Adjust
from imagekit.processors import ResizeToFill
from imagekit.processors import SmartCrop


class Photo(models.Model):
    original_image = models.ImageField(upload_to='photos')

    thumbnail = ImageSpecField([Adjust(contrast=1.2, sharpness=1.1),
            ResizeToFill(50, 50)], image_field='original_image', format='JPEG',
            options={'quality': 90})

    smartcropped_thumbnail = ImageSpecField([Adjust(contrast=1.2,
            sharpness=1.1), SmartCrop(50, 50)], image_field='original_image',
            format='JPEG', options={'quality': 90})


class AbstractImageModel(models.Model):
    original_image = models.ImageField(upload_to='photos')
    abstract_class_spec = ImageSpecField()

    class Meta:
        abstract = True


class ConcreteImageModel1(AbstractImageModel):
    first_spec = ImageSpecField()


class ConcreteImageModel2(AbstractImageModel):
    second_spec = ImageSpecField()
