#!/usr/bin/env python
# encoding: utf-8
"""
tests.py

Tests for django-imagekit.

Created by FI$H 2000 on 2011-09-01.
Copyright (c) 2011 Objects In Space And Time, LLC. All rights reserved.

"""

import os, tempfile
from django.conf import settings

if __name__ == '__main__':
    import imagekit.settings as ik_settings
    ik_settings.__dict__.update({
        "SQ_RUNMODE": 'SQ_SYNC',
        "NOSE_ARGS": ['--rednose', '--nocapture', '--nologcapture'],
    })
    
    settings.configure(**ik_settings.__dict__)
    
    from django.core.management import call_command
    call_command('test', 'imagekit',
        interactive=False, traceback=True, verbosity=2)
    
    tempdata = ik_settings.tempdata
    print "Deleting test data: %s" % tempdata
    os.rmdir(tempdata)
    
    import sys
    sys.exit(0)

from django.core.files.base import ContentFile
from django.db import models
from django.test import TestCase

from imagekit import processors
from imagekit.models import ImageModel, ImageWithMetadata, _storage
from imagekit.specs import ImageSpec
from imagekit.lib import *


class ResizeToWidth(processors.Resize):
    width = 100

class ResizeToHeight(processors.Resize):
    height = 100

class ResizeToFit(processors.Resize):
    width = 100
    height = 100

class ResizeCropped(ResizeToFit):
    crop = ('center', 'center')

class SmartCropped(processors.SmartCrop):
    width = 100
    height = 100

class TransformICC(processors.ICCTransform):
    source = ICCProfile(os.path.join(IK_ROOT, "icc/sRGB-IEC61966-2-1.icc"))
    destination = ICCProfile(os.path.join(IK_ROOT, "icc/adobeRGB-1998.icc"))

class ProofICC(processors.ICCProofTransform):
    source = ICCProfile(os.path.join(IK_ROOT, "icc/sRGB-IEC61966-2-1.icc"))
    destination = ICCProfile(os.path.join(IK_ROOT, "icc/adobeRGB-1998.icc"))
    proof = ICCProfile(os.path.join(IK_ROOT, "icc/CMYK-USWebCoatedSWOP-2.icc"))


class TestResizeToWidth(ImageSpec):
    access_as = 'to_width'
    processors = [ResizeToWidth]

class TestResizeToHeight(ImageSpec):
    access_as = 'to_height'
    processors = [ResizeToHeight]

class TestResizeCropped(ImageSpec):
    access_as = 'cropped'
    processors = [ResizeCropped]

class TestSmartCropped(ImageSpec):
    access_as = 'smartcropped'
    processors = [ResizeToHeight, SmartCropped]

class TestICCTransform(ImageSpec):
    #pre_cache = True
    access_as = 'icctrans'
    processors = [TransformICC]

class TestICCProof(ImageSpec):
    #pre_cache = True
    access_as = 'iccproof'
    processors = [ProofICC]


class TestImage(ImageModel):
    """
    Minimal ImageModel class for testing.
    
    """
    class IKOptions:
        spec_module = 'imagekit.tests'
        storage = _storage
    
    image = models.ImageField(upload_to='testimages', storage=_storage)


class TestImageM(ImageWithMetadata):
    """
    Minimal ImageWithMetadata class for testing.

    """
    class IKOptions:
        spec_module = 'imagekit.tests'
        storage = _storage
    
    image = models.ImageField(upload_to='testmimages', storage=_storage)


def get_image():
    import urllib2, StringIO, random
    urls = [
        'http://ost2.s3.amazonaws.com/images/_uploads/IfThen_Detail_Computron_Orange_2to3_010.jpg',
        'http://ost2.s3.amazonaws.com/images/_uploads/2805163544_1321ee6d30_o.jpg',
        'http://ost2.s3.amazonaws.com/images/_uploads/IfThen_Detail_Computron_Silver_2to3_010.jpg',
        'http://ost2.s3.amazonaws.com/images/_uploads/Josef_Muller_Brockmann_Detail_Lights_2to3_000.jpg',
        'http://ost2.s3.amazonaws.com/images/_uploads/P4141870.jpg',
        'http://ost2.s3.amazonaws.com/images/_uploads/After_The_Quake_Detail_Text_2to3_000.jpg',
        'http://ost2.s3.amazonaws.com/images/_uploads/P4141477.jpg',
        'http://ost2.s3.amazonaws.com/images/_uploads/P4141469.jpg',
        'http://ost2.s3.amazonaws.com/images/_uploads/IMG_1310.jpg',
        'http://ost2.s3.amazonaws.com/images/_uploads/P4141472.jpg',
    ]
    
    random.seed()
    imgurl = random.choice(urls)
    
    if get_image.imgstr is None:
        print "Loading image: %s" % imgurl
        get_image.imgstr = urllib2.urlopen(imgurl).read()
    
    img = Image.open(StringIO.StringIO(get_image.imgstr)).crop((0, 0, 800, 600))
    tmp = tempfile.TemporaryFile()
    img.save(tmp, 'JPEG')
    tmp.seek(0)
    #img.show()
    return tmp

get_image.imgstr = None

class IKTest(TestCase):
    """
    Base TestCase class.
    
    """
    
    def generate_image(self):
        tmp = tempfile.TemporaryFile()
        Image.new('RGB', (800, 600)).save(tmp, 'JPEG')
        tmp.seek(0)
        return tmp
    
    def get_image(self):
        return get_image()
    
    def _get_image(self):
        import urllib2, StringIO, random
        urls = [
            'http://ost2.s3.amazonaws.com/images/_uploads/IfThen_Detail_Computron_Orange_2to3_010.jpg',
            'http://ost2.s3.amazonaws.com/images/_uploads/2805163544_1321ee6d30_o.jpg',
            'http://ost2.s3.amazonaws.com/images/_uploads/IfThen_Detail_Computron_Silver_2to3_010.jpg',
            'http://ost2.s3.amazonaws.com/images/_uploads/Josef_Muller_Brockmann_Detail_Lights_2to3_000.jpg',
            'http://ost2.s3.amazonaws.com/images/_uploads/P4141870.jpg',
            'http://ost2.s3.amazonaws.com/images/_uploads/After_The_Quake_Detail_Text_2to3_000.jpg',
            'http://ost2.s3.amazonaws.com/images/_uploads/P4141477.jpg',
            'http://ost2.s3.amazonaws.com/images/_uploads/P4141469.jpg',
            'http://ost2.s3.amazonaws.com/images/_uploads/IMG_1310.jpg',
            'http://ost2.s3.amazonaws.com/images/_uploads/P4141472.jpg',
        ]
        
        random.seed()
        imgurl = random.choice(urls)
        
        if imgstr is None:
            print "Loading image: %s" % imgurl
            imgstr = urllib2.urlopen(imgurl).read()
        
        img = Image.open(StringIO.StringIO(imgstr)).crop((0, 0, 800, 600))
        tmp = tempfile.TemporaryFile()
        img.save(tmp, 'JPEG')
        tmp.seek(0)
        #img.show()
        return tmp
    
    def setUp(self):
        # dispatch all signals synchronously
        from django.conf import settings
        settings.SQ_RUNMODE = 'SQ_SYNC'
        with self.settings(SQ_RUNMODE='SQ_SYNC'):
            import signalqueue
            queues = backends.ConnectionHandler(settings.SQ_QUEUES, 0)
            signalqueue.worker.queues = queues
            signalqueue.autodiscover()
            
            # image instance for testing
            self.p = TestImage()
            try:
                img = self.get_image()
            except (IOError, AttributeError, ValueError), err:
                print "~~~ Exception thrown DURING SETUP by IKTest.get_image(): %s" % err
                img = self.generate_image()
            self.p.save_image('test.jpeg', ContentFile(img.read()))
            self.p.save()
            img.close()
    
    def test_save_image(self):
        img = self.generate_image()
        
        path = self.p.image.name
        self.p.save_image('test2.jpeg', ContentFile(img.read()))
        self.failIf(self.p._ik.storage.exists(path))
        
        path = self.p.image.name
        img.seek(0)
        self.p.save_image('test.jpeg', ContentFile(img.read()))
        self.failIf(self.p._ik.storage.exists(path))
        
        img.close()
    
    def test_icc_transform(self):
        self.assertTrue(self.p.icctrans.url is not None)
    
    def test_icc_proof_transform(self):
        self.assertTrue(self.p.iccproof.url is not None)
    
    def test_imagewithmetadata(self):
        pm = TestImageM()
        try:
            img = self.get_image()
        except (IOError, AttributeError, ValueError), err:
            print "&&& Exception thrown WHILE TESTING IMAGEWITHMETADATA by IKTest.get_image(): %s" % err
            img = self.generate_image()
        
        pm.save_image('mtest.jpg', ContentFile(img.read()))
        #pm.pilimage.show()
        img.close()
        
        self.assertEqual(pm.image.width, 800)
        self.assertEqual(pm.image.height, 600)
        
        pth = pm.image.name
        pm.save()
        pm.delete(clear_cache=True)
        
        self.failIf(pm._ik.storage.exists(pth))
        
    
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
    
    def test_smartcrop(self):
        self.assertEqual(self.p.smartcropped.width, 100)
        self.assertEqual(self.p.smartcropped.height, 100)
    
    def test_url(self):
        self.assertEqual(
            self.p.to_width.url,
            _storage.url(os.path.join(self.p._ik.cache_dir, self.p.image.name.replace('.jpeg', '_to_width.jpeg'))),
        )
    
    def tearDown(self):
        # make sure image file is deleted
        pth = self.p.image.name
        self.p.delete(clear_cache=True)
        self.failIf(_storage.exists(pth))
    