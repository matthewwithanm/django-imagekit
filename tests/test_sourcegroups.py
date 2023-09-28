import pytest
from django.core.files import File

from imagekit.signals import source_saved
from imagekit.specs.sourcegroups import ImageFieldSourceGroup

from .models import AbstractImageModel, ConcreteImageModel, ImageModel
from .utils import get_image_file


def make_counting_receiver(source_group):
    def receiver(sender, *args, **kwargs):
        if sender is source_group:
            receiver.count += 1
    receiver.count = 0
    return receiver


@pytest.mark.django_db(transaction=True)
def test_source_saved_signal():
    """
    Creating a new instance with an image causes the source_saved signal to be
    dispatched.

    """
    source_group = ImageFieldSourceGroup(ImageModel, 'image')
    receiver = make_counting_receiver(source_group)
    source_saved.connect(receiver)
    with File(get_image_file(), name='reference.png') as image:
        ImageModel.objects.create(image=image)
    assert receiver.count == 1


@pytest.mark.django_db(transaction=True)
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
    assert receiver.count == 0


@pytest.mark.django_db(transaction=True)
def test_abstract_model_signals():
    """
    Source groups created for abstract models must cause signals to be
    dispatched on their concrete subclasses.

    """
    source_group = ImageFieldSourceGroup(AbstractImageModel, 'original_image')
    receiver = make_counting_receiver(source_group)
    source_saved.connect(receiver)
    with File(get_image_file(), name='reference.png') as image:
        ConcreteImageModel.objects.create(original_image=image)
    assert receiver.count == 1
