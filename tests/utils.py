from bs4 import BeautifulSoup
import os
from django.conf import settings
from django.core.files import File
from django.template import Context, Template
from imagekit.lib import Image, StringIO
import pickle
from .models import Photo


def get_image_file():
    """
    See also:

    http://en.wikipedia.org/wiki/Lenna
    http://sipi.usc.edu/database/database.php?volume=misc&image=12

    """
    path = os.path.join(settings.MEDIA_ROOT, 'lenna.png')
    return open(path, 'r+b')


def create_image():
    return Image.open(get_image_file())


def create_instance(model_class, image_name):
    instance = model_class()
    img = File(get_image_file())
    instance.original_image.save(image_name, img)
    instance.save()
    img.close()
    return instance


def create_photo(name):
    return create_instance(Photo, name)


def pickleback(obj):
    pickled = StringIO()
    pickle.dump(obj, pickled)
    pickled.seek(0)
    return pickle.load(pickled)


def render_tag(ttag):
    img = get_image_file()
    template = Template('{%% load imagekit %%}%s' % ttag)
    context = Context({'img': img})
    return template.render(context)


def get_html_attrs(ttag):
    return BeautifulSoup(render_tag(ttag)).img.attrs
