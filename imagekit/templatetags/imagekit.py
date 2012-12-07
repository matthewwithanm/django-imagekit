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


def _generateimage(parser, bits):
    varname = None
    html_bits = []
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


#@register.tag
def generateimage(parser, token):
    """
    Creates an image based on the provided arguments.

    By default::

        {% generateimage 'myapp:thumbnail' from=mymodel.profile_image %}

    generates an ``<img>`` tag::

        <img src="/path/to/34d944f200dd794bf1e6a7f37849f72b.jpg" width="100" height="100" />

    You can add additional attributes to the tag using "with". For example,
    this::

        {% generateimage 'myapp:thumbnail' from=mymodel.profile_image with alt="Hello!" %}

    will result in the following markup::

        <img src="/path/to/34d944f200dd794bf1e6a7f37849f72b.jpg" width="100" height="100" alt="Hello!" />

    For more flexibility, ``generateimage`` also works as an assignment tag::

        {% generateimage 'myapp:thumbnail' from=mymodel.profile_image as th %}
        <img src="{{ th.url }}" width="{{ th.width }}" height="{{ th.height }}" />

    """
    bits = token.split_contents()
    return _generateimage(parser, bits)


#@register.tag
def thumbnail(parser, token):
    """
    A convenient alias for the ``generateimage`` tag with the generator id
    ``'ik:thumbnail'``. The following::

        {% thumbnail from=mymodel.profile_image width=100 height=100 %}

    is equivalent to::

        {% generateimage 'ik:thumbnail' from=mymodel.profile_image width=100 height=100 %}

    The thumbnail tag supports the "with" and "as" bits for adding html
    attributes and assigning to a variable, respectively. It also accepts the
    kwargs "width", "height", "anchor", and "crop".

    To use "smart cropping" (the ``SmartResize`` processor)::

        {% thumbnail from=mymodel.profile_image width=100 height=100 %}

    To crop, anchoring the image to the top right (the ``ResizeToFill``
    processor)::

        {% thumbnail from=mymodel.profile_image width=100 height=100 anchor='tr' %}

    To resize without cropping (using the ``ResizeToFit`` processor)::

        {% thumbnail from=mymodel.profile_image width=100 height=100 crop=0 %}

    """
    # TODO: Support positional arguments for this tag for "from", "width" and "height".
    # Example:
    #     {% thumbnail mymodel.profile_image 100 100 anchor='tl' %}
    bits = token.split_contents()
    bits.insert(1, "'ik:thumbnail'")
    return _generateimage(parser, bits)


generateimage = register.tag(generateimage)
thumbnail = register.tag(thumbnail)
