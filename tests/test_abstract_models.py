from django.core.files import File
from imagekit.signals import source_saved
from imagekit.specs.sourcegroups import ImageFieldSourceGroup
from imagekit.utils import get_nonabstract_descendants
from nose.tools import eq_
from . models import (AbstractImageModel, ConcreteImageModel,
    ConcreteImageModelSubclass)
from .utils import get_image_file


def test_source_saved_signal():
    source_group = ImageFieldSourceGroup(AbstractImageModel, 'original_image')
    count = [0]

    def receiver(sender, *args, **kwargs):
        if sender is source_group:
            count[0] += 1

    source_saved.connect(receiver, dispatch_uid='test_source_saved')
    instance = ConcreteImageModel()
    img = File(get_image_file())
    instance.original_image.save('test_source_saved_signal.jpg', img)

    eq_(count[0], 1)


def test_nonabstract_descendants_generator():
    descendants = list(get_nonabstract_descendants(AbstractImageModel))
    eq_(descendants, [ConcreteImageModel, ConcreteImageModelSubclass])
