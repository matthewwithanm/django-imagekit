from django.core.files import File
from imagekit.signals import source_saved
from imagekit.specs.sourcegroups import ImageFieldSourceGroup
from nose.tools import eq_
from . models import AbstractImageModel, ImageModel, ConcreteImageModel
from .utils import get_image_file


def make_counting_receiver(source_group):
    def receiver(sender, *args, **kwargs):
        if sender is source_group:
            receiver.count += 1
    receiver.count = 0
    return receiver


def test_source_saved_signal():
    """
    Creating a new instance with an image causes the source_saved signal to be
    dispatched.

    """
    source_group = ImageFieldSourceGroup(ImageModel, 'image')
    receiver = make_counting_receiver(source_group)
    source_saved.connect(receiver)
    ImageModel.objects.create(image=File(get_image_file()))
    eq_(receiver.count, 1)


def test_no_source_saved_signal():
    """
    Creating a new instance without an image shouldn't cause the source_saved
    signal to be dispatched.

    https://github.com/matthewwithanm/django-imagekit/issues/214

    """
    source_group = ImageFieldSourceGroup(ImageModel, 'image')
    receiver = make_counting_receiver(source_group)
    source_saved.connect(receiver)
    ImageModel.objects.create()
    eq_(receiver.count, 0)


def test_abstract_model_signals():
    """
    Source groups created for abstract models must cause signals to be
    dispatched on their concrete subclasses.

    """
    source_group = ImageFieldSourceGroup(AbstractImageModel, 'original_image')
    receiver = make_counting_receiver(source_group)
    source_saved.connect(receiver)
    ConcreteImageModel.objects.create(original_image=File(get_image_file()))
    eq_(receiver.count, 1)
