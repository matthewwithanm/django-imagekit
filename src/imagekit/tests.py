import os
import StringIO
import unittest
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.test import TestCase

from models import IKModel
from specs import ImageSpec

from imagekit import Image

IMG_PATH = os.path.join(os.path.dirname(__file__), 'test.jpg')

class TestPhoto(IKModel):
    """ Minimal ImageModel class for testing """
    name = models.CharField(max_length=30)


class PLTest(TestCase):
    """ Base TestCase class """
    def setUp(self):
        Image.new('RGB', (100, 100)).save(IMG_PATH, 'JPEG')
        self.p = TestPhoto(name='landscape')
        self.p.image.save(os.path.basename(IMG_PATH),
                           ContentFile(open(IMG_PATH, 'rb').read()))
        self.p.save()
        
    def test_setup(self):
        self.assert_(self.p.image is not None)
        self.assertEqual(self.p.image.width, 100 )
        
    def test_accessor(self):
        self.assertEqual(self.p.admin_thumbnail.width, 100)

    def tearDown(self):
        os.remove(IMG_PATH)
        path = self.p.image.path
        self.p.delete()
        self.failIf(os.path.isfile(path))
