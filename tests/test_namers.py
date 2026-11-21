import os
from io import BytesIO
from types import SimpleNamespace

import pytest
from django.core.files.storage import FileSystemStorage
from PIL import Image

from imagekit.cachefiles import ImageCacheFile
from imagekit.cachefiles.namers import source_name_dot_hash

from .imagegenerators import TestSpec


@pytest.mark.parametrize('source, expected', [
    (SimpleNamespace(), '.0123456789ab.jpg'),
    (SimpleNamespace(name=None), '.0123456789ab.jpg'),
    (SimpleNamespace(name=''), '.0123456789ab.jpg'),
    (SimpleNamespace(name='photos/bulldog.png'),
     'photos/bulldog.0123456789ab.jpg'),
    (SimpleNamespace(name=os.path.abspath('photos/bulldog.png')),
     'bulldog.0123456789ab.jpg'),
])
def test_source_name_dot_hash(source, expected, settings):
    settings.IMAGEKIT_CACHEFILE_DIR = 'cache'
    generator = SimpleNamespace(
        source=source, format='JPEG',
        get_hash=lambda: '0123456789abcdef0123456789abcdef',
    )

    assert source_name_dot_hash(generator) == os.path.normpath(
        os.path.join('cache', expected)
    )


def test_source_name_dot_hash_generate_unnamed_source(settings, tmp_path):
    settings.IMAGEKIT_SPEC_CACHEFILE_NAMER = (
        'imagekit.cachefiles.namers.source_name_dot_hash'
    )
    source = BytesIO()
    source.name = None
    Image.new('RGB', (2, 3)).save(source, format='PNG')
    source.seek(0)
    spec = TestSpec(source=source)
    spec.format = 'JPEG'
    cachefile = ImageCacheFile(
        spec, storage=FileSystemStorage(location=tmp_path)
    )

    cachefile.generate()

    assert cachefile.storage.exists(cachefile.name)
    with cachefile.storage.open(cachefile.name, 'rb') as generated:
        with Image.open(generated) as image:
            assert image.size == (2, 3)
            assert image.format == 'JPEG'
