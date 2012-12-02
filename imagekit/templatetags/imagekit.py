from django import template
from .compat import parse_bits
from ..files import GeneratedImageCacheFile
from ..registry import generator_registry


register = template.Library()


class GenerateImageAssignmentNode(template.Node):
    _kwarg_map = {
        'from': 'source_file',
    }

    def __init__(self, variable_name, generator_id, **kwargs):
        self.generator_id = generator_id
        self.kwargs = kwargs
        self._variable_name = variable_name

    def get_variable_name(self, context):
        return unicode(self._variable_name)

    def get_kwargs(self, context):
        return dict((self._kwarg_map.get(k, k), v.resolve(context)) for k,
            v in self.kwargs.items())

    def render(self, context):
        from ..utils import autodiscover
        autodiscover()

        variable_name = self.get_variable_name(context)
        generator_id = self.generator_id.resolve(context)
        kwargs = self.get_kwargs(context)
        generator = generator_registry.get(generator_id, **kwargs)
        context[variable_name] = GeneratedImageCacheFile(generator)
        return ''


#@register.tag
def generateimage(parser, token):
    """
    Creates an image based on the provided arguments.

    """

    bits = token.split_contents()
    tag_name = bits.pop(0)

    if bits[-2] == 'as':
        varname = bits[-1]
        bits = bits[:-2]

        # (params, varargs, varkwargs, defaults) = getargspec(g)
        # (params, 'args', 'kwargs', defaults) = getargspec(g)

        args, kwargs = parse_bits(parser, bits,
                ['generator_id'], 'args', 'kwargs', None,
                False, tag_name)
        if len(args) != 1:
            raise template.TemplateSyntaxError("The 'generateimage' tag "
                ' requires exactly one unnamed argument.')
        generator_id = args[0]
        return GenerateImageAssignmentNode(varname, generator_id, **kwargs)
    else:
        raise Exception('!!')
    # elif len(bits) > 1:
    #     return GenerateImageTagNode(
    #         parser.compile_filter(bits[0]),  # spec id
    #         parser.compile_filter(bits[1]),  # source file
    #         bits[2:],                        # html attributes
    #     )
    # else:
    #     raise template.TemplateSyntaxError('\'generateimage\' tags must be in the form'
    #                                        ' "{% generateimage id image %}" or'
    #                                        ' "{% generateimage id image'
    #                                        ' as varname %}"')


generateimage = register.tag(generateimage)
