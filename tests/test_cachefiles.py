from imagekit.cachefiles import ImageCacheFile
from nose.tools import raises
from .imagegenerators import TestSpec
from .utils import assert_file_is_falsy


def test_no_source():
    """
    Ensure sourceless specs are falsy.
    """
    spec = TestSpec(source=None)
    file = ImageCacheFile(spec)
    assert_file_is_falsy(file)


@raises(TestSpec.MissingSource)
def test_no_source_error():
    spec = TestSpec(source=None)
    file = ImageCacheFile(spec)
    file.generate()
