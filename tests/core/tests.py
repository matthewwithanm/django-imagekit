from __future__ import with_statement

import os
import tempfile

from django.core.files.base import ContentFile
from django.db import models
from django.test import TestCase

from imagekit import utils
from imagekit.lib import Image
from imagekit.models import ImageSpec
from imagekit.processors import Adjust
from imagekit.processors.resize import Crop, SmartCrop


class Photo(models.Model):
    original_image = models.ImageField(upload_to='photos')

    thumbnail = ImageSpec([Adjust(contrast=1.2, sharpness=1.1), Crop(50, 50)],
            image_field='original_image', format='JPEG',
            options={'quality': 90})

    smartcropped_thumbnail = ImageSpec([Adjust(contrast=1.2, sharpness=1.1), SmartCrop(50, 50)],
            image_field='original_image', format='JPEG',
            options={'quality': 90})


class IKTest(TestCase):
    def generate_image(self):
        tmp = tempfile.TemporaryFile()
        Image.new('RGB', (800, 600)).save(tmp, 'JPEG')
        tmp.seek(0)
        return tmp

    def generate_lenna(self):
        """
        See also:

        http://en.wikipedia.org/wiki/Lenna
        http://sipi.usc.edu/database/database.php?volume=misc&image=12

        """
        tmp = tempfile.TemporaryFile()
        lennapath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'lenna-800x600-white-border.jpg')
        with open(lennapath, "r+b") as lennafile:
            Image.open(lennafile).save(tmp, 'JPEG')
        tmp.seek(0)
        return tmp

    def create_photo(self, name):
        photo = Photo()
        img = self.generate_lenna()
        file = ContentFile(img.read())
        photo.original_image = file
        photo.original_image.save(name, file)
        photo.save()
        img.close()
        return photo

    def setUp(self):
        self.photo = self.create_photo('test.jpg')

    def test_nodelete(self):
        """Don't delete the spec file when the source image hasn't changed.

        """
        filename = self.photo.thumbnail.file.name
        thumbnail_timestamp = os.path.getmtime(filename)
        self.photo.save()
        self.assertTrue(self.photo.thumbnail.storage.exists(filename))

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
        """ Explicit and smart-cropped thumbnail size """
        self.assertEqual(self.photo.thumbnail.width, 50)
        self.assertEqual(self.photo.thumbnail.height, 50)
        self.assertEqual(self.photo.smartcropped_thumbnail.width, 50)
        self.assertEqual(self.photo.smartcropped_thumbnail.height, 50)

    def test_thumbnail_source_file(self):
        self.assertEqual(
            self.photo.thumbnail.source_file, self.photo.original_image)


class IKUtilsTest(TestCase):
    def test_extension_to_format(self):
        self.assertEqual(utils.extension_to_format('.jpeg'), 'JPEG')
        self.assertEqual(utils.extension_to_format('.rgba'), 'SGI')

        with self.assertRaises(utils.UnknownExtensionError):
            utils.extension_to_format('.txt')

    def test_format_to_extension_no_init(self):
        self.assertEqual(utils.format_to_extension('PNG'), '.png')
        self.assertEqual(utils.format_to_extension('ICO'), '.ico')

        with self.assertRaises(utils.UnknownFormatError):
            utils.format_to_extension('TXT')
