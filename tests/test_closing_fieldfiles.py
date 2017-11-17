from nose.tools import assert_false, assert_true

from .models import Thumbnail
from .utils import create_photo


def test_do_not_leak_open_files():
    instance = create_photo('leak-test.jpg')
    source_file = instance.original_image
    # Ensure the FieldFile is closed before generation
    source_file.close()
    image_generator = Thumbnail(source=source_file)
    image_generator.generate()
    assert_true(source_file.closed)


def test_do_not_close_open_files_after_generate():
    instance = create_photo('do-not-close-test.jpg')
    source_file = instance.original_image
    # Ensure the FieldFile is opened before generation
    source_file.open()
    image_generator = Thumbnail(source=source_file)
    image_generator.generate()
    assert_false(source_file.closed)
    source_file.close()
