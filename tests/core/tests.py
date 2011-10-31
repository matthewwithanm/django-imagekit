import os
import tempfile

from django.core.files.base import ContentFile
from django.db import models
from django.test import TestCase

from imagekit.lib import Image
from imagekit.models import ImageSpec
from imagekit.processors import Adjust
from imagekit.processors.resize import Crop


class Photo(models.Model):
    original_image = models.ImageField(upload_to='photos')
    thumbnail = ImageSpec([Adjust(contrast=1.2, sharpness=1.1), Crop(50, 50)],
            image_field='original_image', format='JPEG', quality=90)


class IKTest(TestCase):
    """ Base TestCase class. """
    def generate_image(self):
        tmp = tempfile.TemporaryFile()
        Image.new('RGB', (800, 600)).save(tmp, 'JPEG')
        tmp.seek(0)
        return tmp

    def setUp(self):
        self.photo = Photo()
        img = self.generate_image()
        file = ContentFile(img.read())
        self.photo.original_image = file
        self.photo.original_image.save('test.jpeg', file)
        self.photo.save()
        img.close()

    def test_save_image(self):
        photo = Photo.objects.get(id=self.photo.id)
        self.assertTrue(os.path.isfile(photo.original_image.path))

    def test_setup(self):
        self.assertEqual(self.photo.original_image.width, 800)
        self.assertEqual(self.photo.original_image.height, 600)

    def test_thumbnail_creation(self):
        photo = Photo.objects.get(id=self.photo.id)
        self.assertTrue(os.path.isfile(photo.thumbnail.file.name))

    def test_thumbnail_size(self):
        self.assertEqual(self.photo.thumbnail.width, 50)
        self.assertEqual(self.photo.thumbnail.height, 50)

    def test_thumbnail_source_file(self):
        self.assertEqual(
            self.photo.thumbnail.source_file, self.photo.original_image)
