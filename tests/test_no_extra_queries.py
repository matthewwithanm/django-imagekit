from nose.tools import assert_false
from mock import Mock, PropertyMock, patch
from .models import Photo


def test_dont_access_source():
    """
    Touching the source may trigger an unneeded query.
    See <https://github.com/matthewwithanm/django-imagekit/issues/295>

    """
    pmock = PropertyMock()
    pmock.__get__ = Mock()
    with patch.object(Photo, 'original_image', pmock):
        photo = Photo()  # noqa
        assert_false(pmock.__get__.called)
