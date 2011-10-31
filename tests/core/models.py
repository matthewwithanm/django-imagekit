from django.db import models

from imagekit.models import ImageModel


class TestPhoto(ImageModel):
    """
    Minimal ImageModel class for testing.

    """
    image = models.ImageField(upload_to='images')

    class IKOptions:
        spec_module = 'core.specs'
