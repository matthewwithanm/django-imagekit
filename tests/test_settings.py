import django
from django.test import override_settings
import pytest
from imagekit.conf import ImageKitConf, settings


@pytest.mark.skipif(
    django.VERSION < (4, 2),
    reason="STORAGES was introduced in Django 4.2",
)
def test_custom_storages():
    with override_settings(
        STORAGES={
            "default": {
                "BACKEND": "tests.utils.CustomStorage",
            }
        },
    ):
        conf = ImageKitConf()
        assert conf.configure_default_file_storage(None) == "tests.utils.CustomStorage"


@pytest.mark.skipif(
    django.VERSION >= (5, 1),
    reason="DEFAULT_FILE_STORAGE is removed in Django 5.1.",
)
def test_custom_default_file_storage():
    with override_settings(DEFAULT_FILE_STORAGE="tests.utils.CustomStorage"):
        # If we don’t remove this, Django 4.2 will keep the old value.
        del settings.STORAGES
        conf = ImageKitConf()
        assert conf.configure_default_file_storage(None) == "tests.utils.CustomStorage"
