from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
from .compat import parse_bits
from ..files import GeneratedImageCacheFile
from ..registry import generator_registry


register = template.Library()


ASSIGNMENT_DELIMETER = 'as'
HTML_ATTRS_DELIMITER = 'with'


_kwarg_map = {
    'from': 'source_file',
}


def get_cache_file(context, generator_id, generator_kwargs):
    generator_id = generator_id.resolve(context)
    kwargs = dict((_kwarg_map.get(k, k), v.resolve(context)) for k,
         v in generator_kwargs.items())
    generator = generator_registry.get(generator_id, **kwargs)
    return GeneratedImageCacheFile(generator)


class GenerateImageAssignmentNode(template.Node):

    def __init__(self, variable_name, generator_id, generator_kwargs):
        self._generator_id = generator_id
        self._generator_kwargs = generator_kwargs
        self._variable_name = variable_name

    def get_variable_name(self, context):
        return unicode(self._variable_name)

    def render(self, context):
        from ..utils import autodiscover
        autodiscover()

        variable_name = self.get_variable_name(context)
        context[variable_name] = get_cache_file(context, self._generator_id,
                self._generator_kwargs)
        return ''


class GenerateImageTagNode(template.Node):

    def __init__(self, generator_id, generator_kwargs, html_attrs):
        self._generator_id = generator_id
        self._generator_kwargs = generator_kwargs
        self._html_attrs = html_attrs

    def render(self, context):
        from ..utils import autodiscover
        autodiscover()

        file = get_cache_file(context, self._generator_id,
                self._generator_kwargs)
        attrs = dict((k, v.resolve(context)) for k, v in
                self._html_attrs.items())

        # Only add width and height if neither is specified (for proportional
        # scaling).
        if not 'width' in attrs and not 'height' in attrs:
            attrs.update(width=file.width, height=file.height)

        attrs['src'] = file.url
        attr_str = ' '.join('%s="%s"' % (escape(k), escape(v)) for k, v in
                attrs.items())
        return mark_safe(u'<img %s />' % attr_str)


#@register.tag
def generateimage(parser, token):
    """
    Creates an image based on the provided arguments.

    """

    varname = None
    html_bits = []
    bits = token.split_contents()
    tag_name = bits.pop(0)

    if bits[-2] == ASSIGNMENT_DELIMETER:
        varname = bits[-1]
        bits = bits[:-2]
    elif HTML_ATTRS_DELIMITER in bits:
        index = bits.index(HTML_ATTRS_DELIMITER)
        html_bits = bits[index + 1:]
        bits = bits[:index]

        if not html_bits:
            raise template.TemplateSyntaxError('Don\'t use "%s" unless you\'re'
                ' setting html attributes.' % HTML_ATTRS_DELIMITER)

    args, kwargs = parse_bits(parser, bits, ['generator_id'], 'args', 'kwargs',
            None, False, tag_name)

    if len(args) != 1:
        raise template.TemplateSyntaxError('The "%s" tag requires exactly one'
                ' unnamed argument (the generator id).' % tag_name)

    generator_id = args[0]

    if varname:
        return GenerateImageAssignmentNode(varname, generator_id, kwargs)
    else:
        html_args, html_kwargs = parse_bits(parser, html_bits, [], 'args',
                'kwargs', None, False, tag_name)
        if len(html_args):
            raise template.TemplateSyntaxError('All "%s" tag arguments after'
                    ' the "%s" token must be named.' % (tag_name,
                    HTML_ATTRS_DELIMITER))
        return GenerateImageTagNode(generator_id, kwargs, html_kwargs)


generateimage = register.tag(generateimage)
