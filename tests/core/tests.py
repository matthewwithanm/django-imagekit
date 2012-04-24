from __future__ import with_statement

import os
import pickle
from StringIO import StringIO

from django.test import TestCase

from imagekit import utils
from .models import (Photo, AbstractImageModel, ConcreteImageModel1,
        ConcreteImageModel2)
from .testutils import generate_lenna, create_photo


class IKTest(TestCase):
    def generate_image(self):
        tmp = tempfile.TemporaryFile()
        Image.new('RGB', (800, 600)).save(tmp, 'JPEG')
        tmp.seek(0)
        return tmp

    def setUp(self):
        self.photo = create_photo('test.jpg')

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


class PickleTest(TestCase):
    def test_source_file(self):
        ph = create_photo('pickletest.jpg')
        pickled_model = StringIO()
        pickle.dump(ph, pickled_model)
        pickled_model.seek(0)
        unpickled_model = pickle.load(pickled_model)

        # This isn't supposed to error.
        unpickled_model.thumbnail.source_file


class InheritanceTest(TestCase):
    def test_abstract_base(self):
        self.assertEqual(set(AbstractImageModel._ik.spec_fields),
                set(['abstract_class_spec']))
        self.assertEqual(set(ConcreteImageModel1._ik.spec_fields),
                set(['abstract_class_spec', 'first_spec']))
        self.assertEqual(set(ConcreteImageModel2._ik.spec_fields),
                set(['abstract_class_spec', 'second_spec']))
