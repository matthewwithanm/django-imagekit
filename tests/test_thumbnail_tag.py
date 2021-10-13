import pytest

from django.template import TemplateSyntaxError
from . import imagegenerators  # noqa
from .utils import render_tag, get_html_attrs, clear_imagekit_cache


def test_img_tag():
    ttag = r"""{% thumbnail '100x100' img %}"""
    clear_imagekit_cache()
    attrs = get_html_attrs(ttag)
    expected_attrs = set(['src', 'width', 'height'])
    assert set(attrs.keys()) == expected_attrs
    for k in expected_attrs:
        assert attrs[k].strip() != ''


def test_img_tag_attrs():
    ttag = r"""{% thumbnail '100x100' img -- alt="Hello" %}"""
    clear_imagekit_cache()
    attrs = get_html_attrs(ttag)
    assert attrs.get('alt') == 'Hello'


def test_dangling_html_attrs_delimiter():
    with pytest.raises(TemplateSyntaxError):
        ttag = r"""{% thumbnail '100x100' img -- %}"""
        render_tag(ttag)


def test_not_enough_args():
    with pytest.raises(TemplateSyntaxError):
        ttag = r"""{% thumbnail '100x100' %}"""
        render_tag(ttag)


def test_too_many_args():
    with pytest.raises(TemplateSyntaxError):
        ttag = r"""{% thumbnail 'generator_id' '100x100' img 'extra' %}"""
        render_tag(ttag)


def test_html_attrs_assignment():
    """
    You can either use thumbnail as an assignment tag or specify html attrs,
    but not both.

    """
    with pytest.raises(TemplateSyntaxError):
        ttag = r"""{% thumbnail '100x100' img -- alt="Hello" as th %}"""
        render_tag(ttag)


def test_assignment_tag():
    ttag = r"""{% thumbnail '100x100' img as th %}{{ th.url }}"""
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
