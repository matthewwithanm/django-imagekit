from unittest.mock import Mock

from django.core.files.storage import FileSystemStorage

from imagekit.cachefiles import ImageCacheFile
from imagekit.cachefiles.backends import Simple as SimpleCFBackend
from imagekit.cachefiles.strategies import Optimistic as OptimisticStrategy

from .utils import create_image


class ImageGenerator:
    def generate(self):
        return create_image()

    def get_hash(self):
        return 'abc123'


def get_image_cache_file():
    storage = Mock(FileSystemStorage)
    backend = SimpleCFBackend()
    strategy = OptimisticStrategy()
    generator = ImageGenerator()
    return ImageCacheFile(generator, storage=storage,
                          cachefile_backend=backend,
                          cachefile_strategy=strategy)


def test_no_io_on_bool():
    """
    When checking the truthiness of an ImageCacheFile, the storage shouldn't
    perform IO operations.

    """
    file = get_image_cache_file()
    bool(file)
    assert not file.storage.exists.called
    assert not file.storage.open.called


def test_no_io_on_url():
    """
    When getting the URL of an ImageCacheFile, the storage shouldn't be
    checked.

    """
    file = get_image_cache_file()
    file.url
    assert not file.storage.exists.called
    assert not file.storage.open.called
