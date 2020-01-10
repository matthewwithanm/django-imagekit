import pytest
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
