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
    
class ResizeToMaxHeight(processors.Resize):
    max_height = 300

class ResizeToOver(processors.Resize):
    max_height = 1000

class ResizeToMaxWidth(processors.Resize):
    max_width = 200

class ResizeToFit(processors.Resize):
    width = 100
    height = 100

class ResizeCropped(ResizeToFit):
    crop = ('center', 'center')

class TestResizeToMaxWidth(ImageSpec):
    access_as = 'to_max_width'
    processors = [ResizeToMaxWidth]
    
class TestResizeToMaxHeight(ImageSpec):
    access_as = 'to_max_height'
    processors = [ResizeToMaxHeight]

class TestResizeToWidth(ImageSpec):
    access_as = 'to_width'
    processors = [ResizeToWidth]

class TestResizeToHeight(ImageSpec):
    access_as = 'to_height'
    processors = [ResizeToHeight]

class TestResizeToOver(ImageSpec):
    access_as = 'to_over'
    processors = [ResizeToOver]

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
        self.p.save_image('test2.jpeg', ContentFile(img.read()))
        img.seek(0)
        self.p.save_image('test.jpeg', ContentFile(img.read()))
        img.close()
    
    def test_setup(self):
        self.assertEqual(self.p.image.width, 800)
        self.assertEqual(self.p.image.height, 600)
    
    def test_to_width(self):
        self.assertEqual(self.p.to_width.width, 100)
        self.assertEqual(self.p.to_width.height, 75)
    
    def test_to_max_over(self):
        self.assertEqual(self.p.to_over.width, 800)
        self.assertEqual(self.p.to_over.height, 600)
    
    def test_to_max_width(self):
        self.assertEqual(self.p.to_max_width.width, 200)
        self.assertEqual(self.p.to_max_width.height, 150)
    
    def test_to_max_height(self):
        self.assertEqual(self.p.to_max_height.width, 400)
        self.assertEqual(self.p.to_max_height.height, 300)
    
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
        self.p.delete()