from __future__ import with_statement

import os

from django.test import TestCase

from imagekit import utils
from .models import (Photo, AbstractImageModel, ConcreteImageModel1,
        ConcreteImageModel2)
from .testutils import create_photo, pickleback


class IKTest(TestCase):

    def setUp(self):
        self.photo = create_photo('test.jpg')

    def test_nodelete(self):
        """Don't delete the spec file when the source image hasn't changed.

        """
        filename = self.photo.thumbnail.file.name
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

        self.assertRaises(utils.UnknownExtensionError,
                lambda: utils.extension_to_format('.txt'))

    def test_format_to_extension_no_init(self):
        self.assertEqual(utils.format_to_extension('PNG'), '.png')
        self.assertEqual(utils.format_to_extension('ICO'), '.ico')

        self.assertRaises(utils.UnknownFormatError,
                lambda: utils.format_to_extension('TXT'))


class PickleTest(TestCase):
    def test_model(self):
        ph = pickleback(create_photo('pickletest.jpg'))

        # This isn't supposed to error.
        ph.thumbnail.source_file

    def test_field(self):
        thumbnail = pickleback(create_photo('pickletest2.jpg').thumbnail)

        # This isn't supposed to error.
        thumbnail.source_file


class InheritanceTest(TestCase):
    def test_abstract_base(self):
        self.assertEqual(set(AbstractImageModel._ik.spec_fields),
                set(['abstract_class_spec']))
        self.assertEqual(set(ConcreteImageModel1._ik.spec_fields),
                set(['abstract_class_spec', 'first_spec']))
        self.assertEqual(set(ConcreteImageModel2._ik.spec_fields),
                set(['abstract_class_spec', 'second_spec']))
