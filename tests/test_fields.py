from django import forms
from django.core.files.base import File
from django.core.files.uploadedfile import SimpleUploadedFile
from imagekit import forms as ikforms
from imagekit.processors import SmartCrop
from nose.tools import eq_
from . import imagegenerators  # noqa
from .models import ProcessedImageFieldModel, ImageModel
from .utils import get_image_file


def test_model_processedimagefield():
    instance = ProcessedImageFieldModel()
    file = File(get_image_file())
    instance.processed.save('whatever.jpeg', file)
    instance.save()

    eq_(instance.processed.width, 50)
    eq_(instance.processed.height, 50)


def test_form_processedimagefield():
    class TestForm(forms.ModelForm):
        image = ikforms.ProcessedImageField(spec_id='tests:testform_image',
                processors=[SmartCrop(50, 50)], format='JPEG')

        class Meta:
            model = ImageModel
            fields = 'image',

    upload_file = get_image_file()
    file_dict = {'image': SimpleUploadedFile('abc.jpg', upload_file.read())}
    form = TestForm({}, file_dict)
    instance = form.save()

    eq_(instance.image.width, 50)
    eq_(instance.image.height, 50)
