from bs4 import BeautifulSoup
from django.template import Context, Template, TemplateSyntaxError
from nose.tools import eq_, assert_not_in, raises, assert_not_equal
from . import imagespecs  # noqa
from .utils import get_image_file


def render_tag(ttag):
    img = get_image_file()
    template = Template('{%% load imagekit %%}%s' % ttag)
    context = Context({'img': img})
    return template.render(context)


def get_html_attrs(ttag):
    return BeautifulSoup(render_tag(ttag)).img.attrs


def test_img_tag():
    ttag = r"""{% generateimage 'testspec' from=img %}"""
    attrs = get_html_attrs(ttag)
    expected_attrs = set(['src', 'width', 'height'])
    eq_(set(attrs.keys()), expected_attrs)
    for k in expected_attrs:
        assert_not_equal(attrs[k].strip(), '')


def test_img_tag_attrs():
    ttag = r"""{% generateimage 'testspec' from=img with alt="Hello" %}"""
    attrs = get_html_attrs(ttag)
    eq_(attrs.get('alt'), 'Hello')


@raises(TemplateSyntaxError)
def test_dangling_with():
    ttag = r"""{% generateimage 'testspec' from=img with %}"""
    render_tag(ttag)


@raises(TemplateSyntaxError)
def test_with_assignment():
    """
    You can either use generateimage as an assigment tag or specify html attrs,
    but not both.

    """
    ttag = r"""{% generateimage 'testspec' from=img with alt="Hello" as th %}"""
    render_tag(ttag)


def test_single_dimension_attr():
    """
    If you only provide one of width or height, the other should not be added.

    """
    ttag = r"""{% generateimage 'testspec' from=img with width="50" %}"""
    attrs = get_html_attrs(ttag)
    assert_not_in('height', attrs)


def test_assignment_tag():
    ttag = r"""{% generateimage 'testspec' from=img as th %} {{ th.url }}"""
    html = render_tag(ttag)
    assert_not_equal(html.strip(), '')
