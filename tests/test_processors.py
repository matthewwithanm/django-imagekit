from imagekit.lib import Image
from imagekit.processors import ResizeToFill, ResizeToFit, SmartCrop
from nose.tools import eq_
from .utils import create_image


def test_smartcrop():
    img = SmartCrop(100, 100).process(create_image())
    eq_(img.size, (100, 100))


def test_resizetofill():
    img = ResizeToFill(100, 100).process(create_image())
    eq_(img.size, (100, 100))


def test_resizetofit():
    # First create an image with aspect ratio 2:1...
    img = Image.new('RGB', (200, 100))

    # ...then resize it to fit within a 100x100 canvas.
    img = ResizeToFit(100, 100).process(img)

    # Assert that the image has maintained the aspect ratio.
    eq_(img.size, (100, 50))


def test_resizetofit_mat():
    img = Image.new('RGB', (200, 100))
    img = ResizeToFit(100, 100, mat_color=0x000000).process(img)
    eq_(img.size, (100, 100))
