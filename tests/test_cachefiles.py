import mock
from django.conf import settings
from hashlib import md5
from imagekit.cachefiles import ImageCacheFile, LazyImageCacheFile
from imagekit.cachefiles.backends import Simple
from imagekit.lib import force_bytes
from nose.tools import raises, eq_
from .imagegenerators import TestSpec
from .utils import (assert_file_is_truthy, assert_file_is_falsy,
                    DummyAsyncCacheFileBackend, get_unique_image_file,
                    get_image_file)


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


def test_repr_does_not_send_existence_required():
    """
    Ensure that `__repr__` method does not send `existance_required` signal

    Cachefile strategy may be configured to generate file on
    `existance_required`.
    To generate images, backend passes `ImageCacheFile` instance to worker.
    Both celery and RQ calls `__repr__` method for each argument to enque call.
    And if `__repr__` of object will send this signal, we will get endless
    recursion

    """
    with mock.patch('imagekit.cachefiles.existence_required') as signal:
        # import here to apply mock
        from imagekit.cachefiles import ImageCacheFile

        spec = TestSpec(source=get_unique_image_file())
        file = ImageCacheFile(
            spec,
            cachefile_backend=DummyAsyncCacheFileBackend()
        )
        file.__repr__()
        eq_(signal.send.called, False)


def test_memcached_cache_key():
    """
    Ensure the default cachefile backend is sanitizing its cache key for
    memcached by default.

    """

    class MockFile(object):
        def __init__(self, name):
            self.name = name

    backend = Simple()
    extra_char_count = len('state-') + len(settings.IMAGEKIT_CACHE_PREFIX)

    length = 199 - extra_char_count
    filename = '1' * length
    file = MockFile(filename)
    eq_(backend.get_key(file), '%s%s-state' %
        (settings.IMAGEKIT_CACHE_PREFIX, file.name))

    length = 200 - extra_char_count
    filename = '1' * length
    file = MockFile(filename)
    eq_(backend.get_key(file), '%s%s:%s' % (
        settings.IMAGEKIT_CACHE_PREFIX,
        '1' * (200 - len(':') - 32 - len(settings.IMAGEKIT_CACHE_PREFIX)),
        md5(force_bytes('%s%s-state' % (settings.IMAGEKIT_CACHE_PREFIX, filename))).hexdigest()))


def test_lazyfile_stringification():
    file = LazyImageCacheFile('testspec', source=None)
    eq_(str(file), '')
    eq_(repr(file), '<ImageCacheFile: None>')

    source_file = get_image_file()
    file = LazyImageCacheFile('testspec', source=source_file)
    file.name = 'a.jpg'
    eq_(str(file), 'a.jpg')
    eq_(repr(file), '<ImageCacheFile: a.jpg>')
