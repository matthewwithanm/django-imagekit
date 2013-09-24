"""
Make sure that the various IK classes can be successfully serialized and
deserialized. This is important when using IK with Celery.

"""

from imagekit.cachefiles import ImageCacheFile
from .imagegenerators import TestSpec
from .utils import create_photo, pickleback, get_unique_image_file


def test_imagespecfield():
    instance = create_photo('pickletest2.jpg')
    thumbnail = pickleback(instance.thumbnail)
    thumbnail.generate()


def test_circular_ref():
    """
    A model instance with a spec field in its dict shouldn't raise a KeyError.

    This corresponds to #234

    """
    instance = create_photo('pickletest3.jpg')
    instance.thumbnail  # Cause thumbnail to be added to instance's __dict__
    pickleback(instance)
	

def test_cachefiles():
    spec = TestSpec(source=get_unique_image_file())
    file = ImageCacheFile(spec)
    file.url
    # remove link to file from spec source generator
    # test __getstate__ of ImageCacheFile
    file.generator.source = None
    pickleback(file)
