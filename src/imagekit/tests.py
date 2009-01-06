import os
import tempfile
import unittest
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.test import TestCase

from models import IKModel
from specs import ImageSpec
from imagekit import processors

from imagekit import Image


class ResizeToWidth(processors.Resize):
    width = 100
    
class ResizeToHeigh(processors.Resize):
    height = 100
    
class ResizeToFit(processors.Resize):
    width = 100
    height = 100
    
class ResizeCrop(ResizeToFit):
    crop = True

class TestResizeToWidth(ImageSpec):
    access_as = 'to_width'
    processors = [ResizeToWidth]


IMG_PATH = os.path.join(os.path.dirname(__file__), 'test.jpg')


class TestPhoto(IKModel):
    """ Minimal ImageModel class for testing """
    image = models.ImageField(upload_to='images')
    
    class IKConfig:
        config_module = 'imagekit.tests'
    

class IKTest(TestCase):
    """ Base TestCase class """
    def setUp(self):
        # create a test image using tempfile and PIL
        self.tmp = tempfile.TemporaryFile()
        Image.new('RGB', (800, 600)).save(self.tmp, 'JPEG')
        self.tmp.seek(0)
        self.p = TestPhoto()
        self.p.image.save(os.path.basename('test.jpg'),
                           ContentFile(self.tmp.read()))
        self.p.save()
        # destroy temp file
        self.tmp.close()
        
    def test_config(self):
        self.assertEqual(self.p._ik.specs, [TestResizeToWidth])
        
    def test_setup(self):
        self.assertEqual(self.p.image.width, 800)
        self.assertEqual(self.p.image.height, 600)
        
    def test_to_width(self):
        self.assertEqual(self.p.to_width.width, 100)
        self.assertEqual(self.p.to_width.height, 75)

    def test_url(self):
        url = "%s/%s" % (self.p.cache_url, 'test_to_width.jpg')
        self.assertEqual(self.p.to_width.url, url)
 
    def tearDown(self):
        # make sure image file is deleted
        path = self.p.image.path
        self.p.delete()
        self.failIf(os.path.isfile(path))
