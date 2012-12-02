from .exceptions import AlreadyRegistered, NotRegistered, MissingGeneratorId
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

    def register(self, generator, id=None):
        # TODO: Should we really allow a nested Config class, since it's not necessarily associated with its container?
        config = getattr(generator, 'Config', None)

        if id is None:
            id = getattr(config, 'id', None)

        if id is None:
            raise MissingGeneratorId('No id provided for %s. You must either'
                                ' pass an id to the register function, or add'
                                ' an id attribute to the inner Config class of'
                                ' your spec or generator.' % generator)

        if id in self._generators:
            raise AlreadyRegistered('The spec or generator with id %s is'
                                    ' already registered' % id)
        self._generators[id] = generator

        source_groups = getattr(config, 'source_groups', None) or []
        source_group_registry.register(id, source_groups)

    def unregister(self, id, generator):
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

    _source_signals = [
        source_created,
        source_changed,
        source_deleted,
    ]

    def __init__(self):
        self._sources = {}
        for signal in self._source_signals:
            signal.connect(self.source_receiver)
        before_access.connect(self.before_access_receiver)

    def register(self, spec_id, sources):
        """
        Associates sources with a spec id

        """
        for source in sources:
            if source not in self._sources:
                self._sources[source] = set()
            self._sources[source].add(spec_id)

    def unregister(self, spec_id, sources):
        """
        Disassociates sources with a spec id

        """
        for source in sources:
            try:
                self._sources[source].remove(spec_id)
            except KeyError:
                continue

    def get(self, spec_id):
        return [source for source in self._sources
                if spec_id in self._sources[source]]

    def before_access_receiver(self, sender, generator, file, **kwargs):
        generator.image_cache_strategy.invoke_callback('before_access', file)

    def source_receiver(self, sender, source_file, signal, info, **kwargs):
        """
        Redirects signals dispatched on sources to the appropriate specs.

        """
        source = sender
        if source not in self._sources:
            return

        for spec in (generator_registry.get(id, source_file=source_file, **info)
                     for id in self._sources[source]):
            event_name = {
                source_created: 'source_created',
                source_changed: 'source_changed',
                source_deleted: 'source_deleted',
            }
            spec._handle_source_event(event_name, source_file)


class Register(object):
    """
    Register specs and sources.

    """
    def spec(self, id, spec):
        generator_registry.register(spec, id)

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
