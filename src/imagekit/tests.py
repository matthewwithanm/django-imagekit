import unittest
from django.test import TestCase

from models import *


class TestPhoto(IKModel):
    """ Minimal ImageModel class for testing """
    name = models.CharField(max_length=30)

class MetaClassTest(TestCase):
    def setUp(self):
        self.p = TestPhoto(name='test')
        
    def test_has_config(self):
        self.assertNotEqual(getattr(self.p, '_ik', None), None, '_ik not found.')

    def tearDown(self):
        pass
