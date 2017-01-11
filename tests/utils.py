from bs4 import BeautifulSoup
import os
import shutil
from django.core.files import File
from django.template import Context, Template
from imagekit.cachefiles.backends import Simple, CacheFileState
from imagekit.conf import settings
from imagekit.lib import Image, StringIO
from imagekit.utils import get_cache
from nose.tools import assert_true, assert_false
import pickle
from tempfile import NamedTemporaryFile
from .models import Photo


def get_image_file():
    """
    See also:

    http://en.wikipedia.org/wiki/Lenna
    http://sipi.usc.edu/database/database.php?volume=misc&image=12
    https://lintian.debian.org/tags/license-problem-non-free-img-lenna.html
    https://github.com/libav/libav/commit/8895bf7b78650c0c21c88cec0484e138ec511a4b
    """
    path = os.path.join(settings.MEDIA_ROOT, 'reference.png')
    return open(path, 'r+b')


def get_unique_image_file():
    file = NamedTemporaryFile()
    file.write(get_image_file().read())
    return file


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


def assert_file_is_falsy(file):
    assert_false(bool(file), 'File is not falsy')


def assert_file_is_truthy(file):
    assert_true(bool(file), 'File is not truthy')


class DummyAsyncCacheFileBackend(Simple):
    """
    A cache file backend meant to simulate async generation.

    """
    is_async = True

    def generate(self, file, force=False):
        pass


def clear_imagekit_cache():
    cache = get_cache()
    cache.clear()
    # Clear IMAGEKIT_CACHEFILE_DIR
    cache_dir = os.path.join(settings.MEDIA_ROOT, settings.IMAGEKIT_CACHEFILE_DIR)
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)


def clear_imagekit_test_files():
    clear_imagekit_cache()
    for fname in os.listdir(settings.MEDIA_ROOT):
        if fname != 'reference.png':
            path = os.path.join(settings.MEDIA_ROOT, fname)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
