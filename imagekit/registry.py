from .exceptions import AlreadyRegistered, NotRegistered
from .signals import (before_access, source_created, source_changed,
                       source_deleted)


class GeneratorRegistry(object):
    """
    An object for registering generators (specs). This registry provides
    a convenient way for a distributable app to define default generators
    without locking the users of the app into it.

    """
    def __init__(self):
        self._generators = {}

    def register(self, id, generator):
        if id in self._generators:
            raise AlreadyRegistered('The spec or generator with id %s is'
                                    ' already registered' % id)
        self._generators[id] = generator

    def unregister(self, id, generator):
        # TODO: Either don't require the generator, or--if we do--assert that it's registered with the provided id
        try:
            del self._generators[id]
        except KeyError:
            raise NotRegistered('The spec or generator with id %s is not'
                                ' registered' % id)

    def get(self, id, **kwargs):
        try:
            generator = self._generators[id]
        except KeyError:
            raise NotRegistered('The spec or generator with id %s is not'
                                ' registered' % id)
        if callable(generator):
            return generator(**kwargs)
        else:
            return generator

    def get_ids(self):
        return self._generators.keys()


class SourceGroupRegistry(object):
    """
    An object for registering source groups with specs. The two are
    associated with each other via a string id. We do this (as opposed to
    associating them directly by, for example, putting a ``source_groups``
    attribute on specs) so that specs can be overridden without losing the
    associated sources. That way, a distributable app can define its own
    specs without locking the users of the app into it.

    """

    _signals = [
        source_created,
        source_changed,
        source_deleted,
    ]

    def __init__(self):
        self._source_groups = {}
        for signal in self._signals:
            signal.connect(self.source_group_receiver)
        before_access.connect(self.before_access_receiver)

    def register(self, spec_id, source_groups):
        """
        Associates source groups with a spec id

        """
        for source_group in source_groups:
            if source_group not in self._source_groups:
                self._source_groups[source_group] = set()
            self._source_groups[source_group].add(spec_id)

    def unregister(self, spec_id, source_groups):
        """
        Disassociates sources with a spec id

        """
        for source_group in source_groups:
            try:
                self._source_groups[source_group].remove(spec_id)
            except KeyError:
                continue

    def get(self, spec_id):
        return [source_group for source_group in self._source_groups
                if spec_id in self._source_groups[source_group]]

    def before_access_receiver(self, sender, generator, file, **kwargs):
        generator.image_cache_strategy.invoke_callback('before_access', file)

    def source_group_receiver(self, sender, source, signal, info, **kwargs):
        """
        Redirects signals dispatched on sources to the appropriate specs.

        """
        source_group = sender
        if source_group not in self._source_groups:
            return

        for spec in (generator_registry.get(id, source=source)
                     for id in self._source_groups[source_group]):
            event_name = {
                source_created: 'source_created',
                source_changed: 'source_changed',
                source_deleted: 'source_deleted',
            }
            spec._handle_source_event(event_name, source)


class Register(object):
    """
    Register specs and sources.

    """
    def spec(self, id, spec=None):
        if spec is None:
            # Return a decorator
            def decorator(cls):
                self.spec(id, cls)
                return cls
            return decorator

        generator_registry.register(id, spec)

    def sources(self, spec_id, sources):
        source_group_registry.register(spec_id, sources)


class Unregister(object):
    """
    Unregister specs and sources.

    """
    def spec(self, id, spec):
        generator_registry.unregister(id, spec)

    def sources(self, spec_id, sources):
        source_group_registry.unregister(spec_id, sources)


generator_registry = GeneratorRegistry()
source_group_registry = SourceGroupRegistry()
register = Register()
unregister = Unregister()
