import pytest
from django import forms
from django.core.files.base import File
from django.core.files.uploadedfile import SimpleUploadedFile

from imagekit import forms as ikforms
from imagekit.processors import SmartCrop

from . import imagegenerators  # noqa
from .models import (ImageModel, ProcessedImageFieldModel,
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
