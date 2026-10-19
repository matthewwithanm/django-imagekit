import pytest
from django import forms
from django.core.files.base import File
from django.core.files.uploadedfile import SimpleUploadedFile

from imagekit import forms as ikforms
from imagekit.processors import SmartCrop

from . import imagegenerators  # noqa
from .models import (ImageModel, ProcessedImageFieldModel,
                     ProcessedImageFieldWithDimensionsModel,
                     ProcessedImageFieldWithSpecModel)
from .utils import get_image_file


@pytest.mark.django_db(transaction=True)
def test_model_processedimagefield():
    instance = ProcessedImageFieldModel()
    with File(get_image_file()) as file:
        instance.processed.save('whatever.jpeg', file)
        instance.save()

    assert instance.processed.width == 50
    assert instance.processed.height == 50


@pytest.mark.django_db(transaction=True)
def test_model_processedimagefield_with_spec():
    instance = ProcessedImageFieldWithSpecModel()
    with File(get_image_file()) as file:
        instance.processed.save('whatever.jpeg', file)
        instance.save()

    assert instance.processed.width == 100
    assert instance.processed.height == 60


@pytest.mark.django_db(transaction=True)
def test_form_processedimagefield():
    class TestForm(forms.ModelForm):
        image = ikforms.ProcessedImageField(spec_id='tests:testform_image',
                                            processors=[SmartCrop(50, 50)],
                                            format='JPEG')

        class Meta:
            model = ImageModel
            fields = 'image',

    with get_image_file() as upload_file:
        files = {
            'image': SimpleUploadedFile('abc.jpg', upload_file.read())
        }

    form = TestForm({}, files)
    instance = form.save()

    assert instance.image.width == 50
    assert instance.image.height == 50


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize('save', [True, False])
def test_processedimagefield_populates_dimension_fields(save):
    instance = ProcessedImageFieldWithDimensionsModel()
    with File(get_image_file()) as file:
        instance.processed.save('dimensions.jpeg', file, save=save)
    assert (instance.width, instance.height) == (50, 30)
    if not save:
        instance.save()
    instance.refresh_from_db()
    assert (instance.width, instance.height) == (50, 30)
    assert (instance.processed.width, instance.processed.height) == (50, 30)


@pytest.mark.django_db(transaction=True)
def test_processedimagefield_dimensions_after_assignment_and_replacement():
    with get_image_file() as file:
        instance = ProcessedImageFieldWithDimensionsModel.objects.create(
            processed=SimpleUploadedFile('assigned.png', file.read()))
    instance.refresh_from_db()
    assert (instance.width, instance.height) == (50, 30)
    instance.width, instance.height = 1, 2
    with get_image_file() as file:
        instance.processed = SimpleUploadedFile('replacement.png', file.read())
        instance.save()
    instance.refresh_from_db()
    assert (instance.width, instance.height) == (50, 30)
