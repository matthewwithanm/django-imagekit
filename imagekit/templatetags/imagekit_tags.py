from django import template
from django.utils.safestring import mark_safe
from ..files import ImageSpecCacheFile
from ..specs import spec_registry


register = template.Library()


class SpecNode(template.Node):
    def __init__(self, spec_id, source_image, variable_name=None):
        self.spec_id = spec_id
        self.source_image = source_image
        self.variable_name = variable_name

    def render(self, context):
        from ..utils import autodiscover
        autodiscover()
        source_image = self.source_image.resolve(context)
        spec_id = self.spec_id.resolve(context)
        spec = spec_registry.get_spec(spec_id)
        if callable(spec):
            spec = spec()
        file = ImageSpecCacheFile(spec, source_image)
        if self.variable_name is not None:
            variable_name = str(self.variable_name)
            context[variable_name] = file
            return ''

        return mark_safe(u'<img src="%s" />' % file.url)


#@register.tag
# TODO: Should this be renamed to something like 'process'?
def spec(parser, token):
    """
    Creates an image based on the provided spec and source image.

    By default::

        {% spec 'myapp:thumbnail', mymodel.profile_image %}

    Generates an ``<img>``::

        <img src="/cache/34d944f200dd794bf1e6a7f37849f72b.jpg" />

    Storing it as a context variable allows more flexibility::

        {% spec 'myapp:thumbnail' mymodel.profile_image as th %}
        <img src="{{ th.url }}" width="{{ th.width }}" height="{{ th.height }}" />

    """

    args = token.split_contents()
    arg_count = len(args)

    if (arg_count < 3 or arg_count > 5
        or (arg_count > 3 and arg_count < 5)
        or (args == 5 and args[3] != 'as')):
        raise template.TemplateSyntaxError('\'spec\' tags must be in the form'
                                           ' "{% spec spec_id image %}" or'
                                           ' "{% spec spec_id image'
                                           ' as varname %}"')

    spec_id = parser.compile_filter(args[1])
    source_image = parser.compile_filter(args[2])
    variable_name = arg_count > 3 and args[4] or None
    return SpecNode(spec_id, source_image, variable_name)


spec = spec_tag = register.tag(spec)
