"""
Make sure that the various IK classes can be successfully serialized and
deserialized. This is important when using IK with Celery.

"""

from .utils import create_photo, pickleback


def test_imagespecfield():
    instance = create_photo('pickletest2.jpg')
    thumbnail = pickleback(instance.thumbnail)
    thumbnail.generate()
