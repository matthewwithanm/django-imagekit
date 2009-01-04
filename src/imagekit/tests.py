import os
import StringIO
import unittest
from django.conf import settings
from django.core.files.base import ContentFile
from django.test import TestCase

from models import IKModel
from specs import ImageSpec


# Required PIL classes may or may not be available from the root namespace
# depending on the installation method used.
try:
    import Image
    import ImageFile
    import ImageFilter
    import ImageEnhance
except ImportError:
    try:
        from PIL import Image
        from PIL import ImageFile
        from PIL import ImageFilter
        from PIL import ImageEnhance
    except ImportError:
        raise ImportError(_('Photologue was unable to import the Python Imaging Library. Please confirm it`s installed and available on your current Python path.'))

class TestPhoto(IKModel):
    """ Minimal ImageModel class for testing """
    name = models.CharField(max_length=30)


class PLTest(TestCase):
    """ Base TestCase class """
    def setUp(self):
        imgfile = StringIO.StringIO()
        Image.new('RGB', (100, 100)).save(imgfile, 'JPEG')
        
        content_file = ContentFile(imgfile.read())
        
        self.p = TestPhoto(name='landscape')
        self.p.image.save('image.jpeg', content_file)
        self.p.save()
        
    def test_setup(self):
        self.assert_(self.p.image is not None)
        self.assertEqual(self.p.image.width, 100 )
        
    def test_accessor(self):
        pass
        self.assertEqual(self.p.thumbnail.siz)

    def tearDown(self):
        path = self.p.image.path
        
        os.remove(path)
        return
        
        self.p.delete()
        self.failIf(os.path.isfile(path))
