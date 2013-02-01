from django.template import TemplateSyntaxError
from nose.tools import eq_, raises, assert_not_equal
from . import imagegenerators  # noqa
from .utils import render_tag, get_html_attrs


def test_img_tag():
    ttag = r"""{% thumbnail '100x100' img %}"""
    attrs = get_html_attrs(ttag)
    expected_attrs = set(['src', 'width', 'height'])
    eq_(set(attrs.keys()), expected_attrs)
    for k in expected_attrs:
        assert_not_equal(attrs[k].strip(), '')


def test_img_tag_attrs():
    ttag = r"""{% thumbnail '100x100' img -- alt="Hello" %}"""
    attrs = get_html_attrs(ttag)
    eq_(attrs.get('alt'), 'Hello')


@raises(TemplateSyntaxError)
def test_dangling_html_attrs_delimiter():
    ttag = r"""{% thumbnail '100x100' img -- %}"""
    render_tag(ttag)


@raises(TemplateSyntaxError)
def test_not_enough_args():
    ttag = r"""{% thumbnail '100x100' %}"""
    render_tag(ttag)


@raises(TemplateSyntaxError)
def test_too_many_args():
    ttag = r"""{% thumbnail 'generator_id' '100x100' img 'extra' %}"""
    render_tag(ttag)


@raises(TemplateSyntaxError)
def test_html_attrs_assignment():
    """
    You can either use thumbnail as an assigment tag or specify html attrs,
    but not both.

    """
    ttag = r"""{% thumbnail '100x100' img -- alt="Hello" as th %}"""
    render_tag(ttag)


def test_assignment_tag():
    ttag = r"""{% thumbnail '100x100' img as th %}{{ th.url }}"""
    html = render_tag(ttag)
    assert_not_equal(html, '')


def test_single_dimension():
    ttag = r"""{% thumbnail '100x' img as th %}{{ th.width }}"""
    html = render_tag(ttag)
    eq_(html, '100')


def test_alternate_generator():
    ttag = r"""{% thumbnail '1pxsq' '100x' img as th %}{{ th.width }}"""
    html = render_tag(ttag)
    eq_(html, '1')
