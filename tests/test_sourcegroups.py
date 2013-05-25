from django.core.files import File
from imagekit.signals import source_saved
from imagekit.specs.sourcegroups import ImageFieldSourceGroup
from nose.tools import eq_
from . models import AbstractImageModel, ConcreteImageModel
from .utils import get_image_file


def make_counting_receiver(source_group):
    def receiver(sender, *args, **kwargs):
        if sender is source_group:
            receiver.count += 1
    receiver.count = 0
    return receiver


def test_abstract_model_signals():
    """
    Source groups created for abstract models must cause signals to be
    dispatched on their concrete subclasses.

    """
    source_group = ImageFieldSourceGroup(AbstractImageModel, 'original_image')
    receiver = make_counting_receiver(source_group)
    source_saved.connect(receiver)
    instance = ConcreteImageModel()
    img = File(get_image_file())
    instance.original_image.save('test_source_saved_signal.jpg', img)
    eq_(receiver.count, 1)
