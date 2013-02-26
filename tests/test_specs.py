from imagekit.cachefiles import ImageCacheFile
from nose.tools import assert_false
from .imagegenerators import TestSpec


def test_no_source():
    """
    Ensure sourceless specs are falsy.
    """
    spec = TestSpec(source=None)
    file = ImageCacheFile(spec)
    assert_false(bool(file))
