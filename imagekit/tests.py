import os
import tempfile
import unittest
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.test import TestCase

from imagekit import processors
from imagekit.models import ImageModel
from imagekit.specs import ImageSpec
from imagekit.lib import Image


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

class TestPhoto(ImageModel):
    """ Minimal ImageModel class for testing """
    image = models.ImageField(upload_to='images')

    class IKOptions:
        spec_module = 'imagekit.tests'


class IKTest(TestCase):
    """ Base TestCase class """
    def generate_image(self):
        tmp = tempfile.TemporaryFile()
        Image.new('RGB', (800, 600)).save(tmp, 'JPEG')
        tmp.seek(0)
        return tmp

    def setUp(self):
        self.p = TestPhoto()
        img = self.generate_image()
        self.p.save_image('test.jpeg', ContentFile(img.read()))
        self.p.save()
        img.close()

    def test_save_image(self):
        img = self.generate_image()
        path = self.p.image.path
        self.p.save_image('test2.jpeg', ContentFile(img.read()))
        self.failIf(os.path.isfile(path))
        path = self.p.image.path
        img.seek(0)
        self.p.save_image('test.jpeg', ContentFile(img.read()))
        self.failIf(os.path.isfile(path))
        img.close()

    def test_setup(self):
        self.assertEqual(self.p.image.width, 800)
        self.assertEqual(self.p.image.height, 600)

    def test_to_width(self):
        self.assertEqual(self.p.to_width.width, 100)
        self.assertEqual(self.p.to_width.height, 75)

    def test_to_height(self):
        self.assertEqual(self.p.to_height.width, 133)
        self.assertEqual(self.p.to_height.height, 100)

    def test_crop(self):
        self.assertEqual(self.p.cropped.width, 100)
        self.assertEqual(self.p.cropped.height, 100)

    def test_url(self):
        tup = (settings.MEDIA_URL, self.p._ik.cache_dir,
               'images/test_to_width.jpeg')
        self.assertEqual(self.p.to_width.url, "%s%s/%s" % tup)

    def tearDown(self):
        # make sure image file is deleted
        path = self.p.image.path
        self.p.delete()
        self.failIf(os.path.isfile(path))
