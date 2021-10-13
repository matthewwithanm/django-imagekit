import pytest

from .utils import clear_imagekit_test_files


@pytest.fixture(scope='session', autouse=True)
def imagekit_test_files_teardown(request):
    request.addfinalizer(clear_imagekit_test_files)
