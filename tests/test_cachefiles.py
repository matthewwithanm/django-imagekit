from imagekit.cachefiles import ImageCacheFile
from nose.tools import raises
from .imagegenerators import TestSpec
from .utils import (assert_file_is_truthy, assert_file_is_falsy,
                    DummyAsyncCacheFileBackend, get_unique_image_file)


def test_no_source_falsiness():
    """
    Ensure cache files generated from sourceless specs are falsy.

    """
    spec = TestSpec(source=None)
    file = ImageCacheFile(spec)
    assert_file_is_falsy(file)


def test_sync_backend_truthiness():
    """
    Ensure that a cachefile with a synchronous cache file backend (the default)
    is truthy.

    """
    spec = TestSpec(source=get_unique_image_file())
    file = ImageCacheFile(spec)
    assert_file_is_truthy(file)


def test_async_backend_falsiness():
    """
    Ensure that a cachefile with an asynchronous cache file backend is falsy.

    """
    spec = TestSpec(source=get_unique_image_file())
    file = ImageCacheFile(spec, cachefile_backend=DummyAsyncCacheFileBackend())
    assert_file_is_falsy(file)


@raises(TestSpec.MissingSource)
def test_no_source_error():
    spec = TestSpec(source=None)
    file = ImageCacheFile(spec)
    file.generate()
