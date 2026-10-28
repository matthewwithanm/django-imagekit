import pytest
import re
from django.template import TemplateSyntaxError

from . import imagegenerators  # noqa
from .utils import clear_imagekit_cache, get_html_attrs, render_tag


def test_img_tag():
    ttag = r"""{% thumbnail '100x100' img %}"""
    clear_imagekit_cache()
    attrs = get_html_attrs(ttag)
    expected_attrs = {'src', 'width', 'height'}
    assert set(attrs.keys()) == expected_attrs
    for k in expected_attrs:
        assert attrs[k].strip() != ''


def test_img_tag_anchor():
    ttag = r"""{% thumbnail '100x100' img anchor='c' %}"""
    clear_imagekit_cache()
    attrs = get_html_attrs(ttag)
    expected_attrs = {'src', 'width', 'height'}
    assert set(attrs.keys()) == expected_attrs
    for k in expected_attrs:
        assert attrs[k].strip() != ''


def test_img_tag_attrs():
    ttag = r"""{% thumbnail '100x100' img -- alt="Hello" %}"""
    clear_imagekit_cache()
    attrs = get_html_attrs(ttag)
    assert attrs.get('alt') == 'Hello'


def test_dangling_html_attrs_delimiter():
    ttag = r"""{% thumbnail '100x100' img -- %}"""
    with pytest.raises(TemplateSyntaxError):
        render_tag(ttag)


def test_not_enough_args():
    ttag = r"""{% thumbnail '100x100' %}"""
    with pytest.raises(TemplateSyntaxError):
        render_tag(ttag)


def test_too_many_args():
    ttag = r"""{% thumbnail 'generator_id' '100x100' img 'extra' %}"""
    with pytest.raises(TemplateSyntaxError):
        render_tag(ttag)


def test_html_attrs_assignment():
    """
    You can either use thumbnail as an assignment tag or specify html attrs,
    but not both.

    """
    ttag = r"""{% thumbnail '100x100' img -- alt="Hello" as th %}"""
    with pytest.raises(TemplateSyntaxError):
        render_tag(ttag)


def test_assignment_tag():
    ttag = r"""{% thumbnail '100x100' img as th %}{{ th.url }}"""
    clear_imagekit_cache()
    html = render_tag(ttag)
    assert html != ''


def test_assignment_tag_anchor():
    ttag = r"""{% thumbnail '100x100' img anchor='c' as th %}{{ th.url }}"""
    clear_imagekit_cache()
    html = render_tag(ttag)
    assert html != ''


def test_single_dimension():
    ttag = r"""{% thumbnail '100x' img as th %}{{ th.width }}"""
    clear_imagekit_cache()
    html = render_tag(ttag)
    assert html == '100'


def test_alternate_generator():
    ttag = r"""{% thumbnail '1pxsq' '100x' img as th %}{{ th.width }}"""
    clear_imagekit_cache()
    html = render_tag(ttag)
    assert html == '1'


def test_srcset_arg():
    ttag = r"""{% thumbnail '100x' img srcset="1.5 2" %}"""
    clear_imagekit_cache()
    html = render_tag(ttag)
    srcset_regex = re.compile('srcset=".* 1x ,.* 1\\.5x ,.* 2.0x"')
    assert srcset_regex.search(html) is not None


def test_alternate_format():
    ttag = r"""{% thumbnail '100x' img format='webp' as th %}{{ th.url }}"""
    clear_imagekit_cache()
    html = render_tag(ttag)
    assert html.endswith('webp')


@pytest.mark.parametrize('suffix', ['', 'srcset="2"', '-- width="100"'])
def test_missing_source_does_not_break_template(tmp_path, suffix):
    from django.core.files.storage import FileSystemStorage
    from django.db.models import ImageField
    from django.template import Context, Template

    clear_imagekit_cache()
    field = ImageField(storage=FileSystemStorage(location=tmp_path))
    source = field.attr_class(None, field, 'missing-source.png')
    template = Template('{% load imagekit %}before'
                        "{% thumbnail '100x100' img " + suffix + ' %}after')
    assert template.render(Context({'img': source})) == 'beforeafter'


def test_missing_assigned_thumbnail_dimensions_are_silent(tmp_path):
    from django.core.files.storage import FileSystemStorage
    from django.db.models import ImageField
    from django.template import Context, Template

    clear_imagekit_cache()
    field = ImageField(storage=FileSystemStorage(location=tmp_path))
    source = field.attr_class(None, field, 'missing-source.png')
    template = Template('{% load imagekit %}before'
                        "{% thumbnail '100x100' img as th %}{{ th.width }}after")
    assert template.render(Context({'img': source})) == 'beforeafter'


@pytest.mark.parametrize('exception', [PermissionError('denied'), OSError('unavailable')])
def test_source_storage_errors_are_not_silenced(tmp_path, exception):
    from django.core.files.storage import FileSystemStorage
    from django.db.models import ImageField
    from django.template import Context, Template

    class FailingStorage(FileSystemStorage):
        def _open(self, name, mode='rb'):
            raise exception

    clear_imagekit_cache()
    field = ImageField(storage=FailingStorage(location=tmp_path))
    source = field.attr_class(None, field, 'unavailable-source.png')
    template = Template('{% load imagekit %}'
                        "{% thumbnail '100x100' img %}")
    with pytest.raises(type(exception), match=str(exception)):
        template.render(Context({'img': source}))


def test_processor_file_error_is_not_silenced():
    from unittest.mock import patch

    clear_imagekit_cache()
    with patch('imagekit.specs.process_image', side_effect=FileNotFoundError('processor data')):
        with pytest.raises(FileNotFoundError, match='processor data'):
            render_tag("{% thumbnail '100x100' img %}")
