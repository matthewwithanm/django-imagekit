import django
from django.test import override_settings
import pytest
from imagekit.utils import get_storage


def test_get_storage_default():
    from django.core.files.storage import default_storage

    if django.VERSION >= (4, 2):
        assert get_storage() == default_storage
    else:
        assert isinstance(get_storage(), type(default_storage._wrapped))


@pytest.mark.skipif(
    django.VERSION >= (5, 1),
    reason="DEFAULT_FILE_STORAGE is removed in Django 5.1.",
)
def test_get_storage_custom_import_path():
    from tests.utils import CustomStorage

    with override_settings(IMAGEKIT_DEFAULT_FILE_STORAGE="tests.utils.CustomStorage"):
        assert isinstance(get_storage(), CustomStorage)


@pytest.mark.skipif(
    django.VERSION < (4, 2),
    reason="STORAGES was introduced in Django 4.2",
)
def test_get_storage_custom_key():
    from tests.utils import CustomStorage

    with override_settings(
        STORAGES={
            "custom": {
                "BACKEND": "tests.utils.CustomStorage",
            }
        },
        IMAGEKIT_DEFAULT_FILE_STORAGE="custom",
    ):
        assert isinstance(get_storage(), CustomStorage)
