from django import template
from django.utils.safestring import mark_safe
import re
from ..files import ImageSpecCacheFile
from .. import specs


register = template.Library()


html_attr_pattern = r"""
    (?P<name>\w+)          # The attribute name
    (
        \s*=\s*            # an equals sign, that may or may not have spaces around it
        (?P<value>
            ("[^"]*")      # a double-quoted value
            |              # or
            ('[^']*')      # a single-quoted value
            |              # or
            ([^"'<>=\s]+)  # an unquoted value
        )
    )?
"""

html_attr_re = re.compile(html_attr_pattern, re.VERBOSE)


class SpecResultNodeMixin(object):
    def __init__(self, spec_id, source_file):
        self._spec_id = spec_id
        self._source_file = source_file

    def get_spec(self, context):
        from ..utils import autodiscover
        autodiscover()
        spec_id = self._spec_id.resolve(context)
        spec = specs.registry.get_spec(spec_id)
        if callable(spec):
            spec = spec()
        return spec

    def get_source_file(self, context):
        return self._source_file.resolve(context)

    def get_file(self, context):
        spec = self.get_spec(context)
        source_file = self.get_source_file(context)
        return ImageSpecCacheFile(spec, source_file)


class SpecResultAssignmentNode(template.Node, SpecResultNodeMixin):
    def __init__(self, spec_id, source_file, variable_name):
        super(SpecResultAssignmentNode, self).__init__(spec_id, source_file)
        self._variable_name = variable_name

    def get_variable_name(self, context):
        return unicode(self._variable_name)

    def render(self, context):
        variable_name = self.get_variable_name(context)
        context[variable_name] = self.get_file(context)
        return ''


class SpecResultImgTagNode(template.Node, SpecResultNodeMixin):
    def __init__(self, spec_id, source_file, html_attrs):
        super(SpecResultImgTagNode, self).__init__(spec_id, source_file)
        self._html_attrs = html_attrs

    def get_html_attrs(self, context):
        attrs = []
        for attr in self._html_attrs:
            match = html_attr_re.search(attr)
            if match:
                attrs.append((match.group('name'), match.group('value')))
        return attrs

    def get_attr_str(self, k, v):
        return k if v is None else '%s=%s' % (k, v)

    def render(self, context):
        file = self.get_file(context)
        attrs = self.get_html_attrs(context)
        attr_dict = dict(attrs)
        if not 'width' in attr_dict and not 'height' in attr_dict:
            attrs = attrs + [('width', '"%s"' % file.width),
                             ('height', '"%s"' % file.height)]
        attrs = [('src', '"%s"' % file.url)] + attrs
        attr_str = ' '.join(self.get_attr_str(k, v) for k, v in attrs)
        return mark_safe(u'<img %s />' % attr_str)


#@register.tag
# TODO: Should this be renamed to something like 'process'?
def spec(parser, token):
    """
    Creates an image based on the provided spec and source image.

    By default::

        {% spec 'myapp:thumbnail' mymodel.profile_image %}

    Generates an ``<img>``::

        <img src="/cache/34d944f200dd794bf1e6a7f37849f72b.jpg" />

    Storing it as a context variable allows more flexibility::

        {% spec 'myapp:thumbnail' mymodel.profile_image as th %}
        <img src="{{ th.url }}" width="{{ th.width }}" height="{{ th.height }}" />

    """

    bits = token.split_contents()
    tag_name = bits.pop(0)

    if len(bits) == 4 and bits[2] == 'as':
        return SpecResultAssignmentNode(
            parser.compile_filter(bits[0]),  # spec id
            parser.compile_filter(bits[1]),  # source file
            parser.compile_filter(bits[3]),  # var name
        )
    elif len(bits) > 1:
        return SpecResultImgTagNode(
            parser.compile_filter(bits[0]),  # spec id
            parser.compile_filter(bits[1]),  # source file
            bits[2:],                        # html attributes
        )
    else:
        raise template.TemplateSyntaxError('\'spec\' tags must be in the form'
                                           ' "{% spec spec_id image %}" or'
                                           ' "{% spec spec_id image'
                                           ' as varname %}"')


spec = spec_tag = register.tag(spec)
