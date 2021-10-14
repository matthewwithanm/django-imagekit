import pytest
from django.template import TemplateSyntaxError

from . import imagegenerators  # noqa
from .utils import clear_imagekit_cache, get_html_attrs, render_tag


def test_img_tag():
    ttag = r"""{% generateimage 'testspec' source=img %}"""
    clear_imagekit_cache()
    attrs = get_html_attrs(ttag)
    expected_attrs = {'src', 'width', 'height'}
    assert set(attrs.keys()) == expected_attrs
    for k in expected_attrs:
        assert attrs[k].strip() != ''


def test_img_tag_attrs():
    ttag = r"""{% generateimage 'testspec' source=img -- alt="Hello" %}"""
    clear_imagekit_cache()
    attrs = get_html_attrs(ttag)
    assert attrs.get('alt') == 'Hello'


def test_dangling_html_attrs_delimiter():
    ttag = r"""{% generateimage 'testspec' source=img -- %}"""
    with pytest.raises(TemplateSyntaxError):
        render_tag(ttag)


def test_html_attrs_assignment():
    """
    You can either use generateimage as an assignment tag or specify html attrs,
    but not both.

    """
    ttag = r"""{% generateimage 'testspec' source=img -- alt="Hello" as th %}"""
    with pytest.raises(TemplateSyntaxError):
        render_tag(ttag)


def test_single_dimension_attr():
    """
    If you only provide one of width or height, the other should not be added.

    """
    ttag = r"""{% generateimage 'testspec' source=img -- width="50" %}"""
    clear_imagekit_cache()
    attrs = get_html_attrs(ttag)
    assert 'height' not in attrs


def test_assignment_tag():
    ttag = r"""{% generateimage 'testspec' source=img as th %}{{ th.url }}{{ th.height }}{{ th.width }}"""
    clear_imagekit_cache()
    html = render_tag(ttag)
    assert html.strip() != ''
