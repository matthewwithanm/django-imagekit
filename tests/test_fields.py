from django.core.files.base import File
from nose.tools import eq_
from . import imagespecs  # noqa
from .models import ProcessedImageFieldModel
from .utils import get_image_file


def test_model_processedimagefield():
    instance = ProcessedImageFieldModel()
    file = File(get_image_file())
    instance.processed.save('whatever.jpeg', file)
    instance.save()

    eq_(instance.processed.width, 50)
    eq_(instance.processed.height, 50)
