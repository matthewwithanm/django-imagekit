import os
import tempfile

from django.core.files.base import ContentFile

from imagekit.lib import Image
from .models import Photo


def generate_lenna():
    """
    See also:

    http://en.wikipedia.org/wiki/Lenna
    http://sipi.usc.edu/database/database.php?volume=misc&image=12

    """
    tmp = tempfile.TemporaryFile()
    lennapath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'lenna-800x600-white-border.jpg')
    with open(lennapath, "r+b") as lennafile:
        Image.open(lennafile).save(tmp, 'JPEG')
    tmp.seek(0)
    return tmp


def create_instance(model_class, image_name):
    instance = model_class()
    img = generate_lenna()
    file = ContentFile(img.read())
    instance.original_image = file
    instance.original_image.save(image_name, file)
    instance.save()
    img.close()
    return instance


def create_photo(name):
    return create_instance(Photo, name)
