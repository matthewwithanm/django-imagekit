from django import forms
from imagekit.forms import ImageProcessingField
from imagekit.processors import ResizeToFill
from .models import Photo


class TestForm(forms.ModelForm):
    original_image = ImageProcessingField([ResizeToFill(100, 100)])

    class Meta:
        model = Photo
