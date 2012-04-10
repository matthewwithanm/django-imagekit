import os
from django import template

from ..files import ImageSpecFile


register = template.Library()


class AlreadyRegistered(Exception):
    pass


class NotRegistered(Exception):
    pass


class SpecRegistry(object):
    def __init__(self):
        self._specs = {}

    def register(self, id, spec):
        if id in self._specs:
            raise AlreadyRegistered('The spec with id %s is already registered' % id)
        self._specs[id] = spec

    def unregister(self, id, spec):
        try:
            del self._specs[id]
        except KeyError:
            raise NotRegistered('The spec with id %s is not registered' % id)

    def get_spec(self, id):
        try:
            return self._specs[id]
        except KeyError:
            raise NotRegistered('The spec with id %s is not registered' % id)


spec_registry = SpecRegistry()


class SpecNode(template.Node):
    def __init__(self, spec_id, source_image, variable_name):
        self.spec_id = spec_id
        self.source_image = source_image
        self.variable_name = variable_name

    def _default_cache_to(self, instance, path, specname, extension):
        """
        Determines the filename to use for the transformed image. Can be
        overridden on a per-spec basis by setting the cache_to property on
        the spec.

        """
        filepath, basename = os.path.split(path)
        filename = os.path.splitext(basename)[0]
        new_name = '%s_%s%s' % (filename, specname, extension)
        return os.path.join(os.path.join('cache', filepath), new_name)

    def render(self, context):
        from ..utils import autodiscover
        autodiscover()
        source_image = self.source_image.resolve(context)
        variable_name = str(self.variable_name)
        spec_id = self.spec_id.resolve(context)
        spec = spec_registry.get_spec(spec_id)
        if callable(spec):
            spec = spec()
        context[variable_name] = ImageSpecFile(spec, source_image, spec_id)
        return ''


#@register.tag
def spec(parser, token):
    """
    Creates an image based on the provided spec and source image and sets it
    as a context variable:

        {% spec 'myapp:thumbnail' mymodel.profile_image as th %}
        <img src="{{ th.url }}" width="{{ th.width }}" height="{{ th.height }}" />

    """

    args = token.split_contents()

    if len(args) != 5 or args[3] != 'as':
        raise TemplateSyntaxError('\'spec\' tags must be in the form "{% spec spec_id image as varname %}"')

    return SpecNode(*[parser.compile_filter(arg) for arg in args[1:3] \
            + [args[4]]])


spec = spec_tag = register.tag(spec)


def _register_spec(id, spec=None):
    if not spec:
        def decorator(cls):
            spec_registry.register(id, cls)
            return cls
        return decorator
    spec_registry.register(id, spec)


def _unregister_spec(id, spec):
    spec_registry.unregister(id, spec)


spec_tag.register = _register_spec
spec_tag.unregister = _unregister_spec
