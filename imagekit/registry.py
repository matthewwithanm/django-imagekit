from .exceptions import AlreadyRegistered, NotRegistered
from .signals import before_access, source_created, source_changed, source_deleted
from .utils import call_strategy_method


class GeneratorRegistry(object):
    """
    An object for registering generators. This registry provides
    a convenient way for a distributable app to define default generators
    without locking the users of the app into it.

    """
    def __init__(self):
        self._generators = {}
        before_access.connect(self.before_access_receiver)

    def register(self, id, generator):
        if id in self._generators:
            raise AlreadyRegistered('The generator with id %s is'
                                    ' already registered' % id)
        self._generators[id] = generator

    def unregister(self, id, generator):
        # TODO: Either don't require the generator, or--if we do--assert that it's registered with the provided id
        try:
            del self._generators[id]
        except KeyError:
            raise NotRegistered('The generator with id %s is not'
                                ' registered' % id)

    def get(self, id, **kwargs):
        try:
            generator = self._generators[id]
        except KeyError:
            raise NotRegistered('The generator with id %s is not'
                                ' registered' % id)
        if callable(generator):
            return generator(**kwargs)
        else:
            return generator

    def get_ids(self):
        return self._generators.keys()

    def before_access_receiver(self, sender, file, **kwargs):
        generator = file.generator

        # FIXME: I guess this means you can't register functions?
        if generator.__class__ in self._generators.values():
            # Only invoke the strategy method for registered generators.
            call_strategy_method(generator, 'before_access', file=file)


class SourceGroupRegistry(object):
    """
    The source group registry is responsible for listening to source_* signals
    on source groups, and relaying them to the image generator strategies of the
    appropriate generators.

    In addition, registering a new source group also registers its generated
    files with that registry.

    """
    _signals = {
        source_created: 'on_source_created',
        source_changed: 'on_source_changed',
        source_deleted: 'on_source_deleted',
    }

    def __init__(self):
        self._source_groups = {}
        for signal in self._signals.keys():
            signal.connect(self.source_group_receiver)

    def register(self, generator_id, source_group):
        from .specs.sourcegroups import SourceGroupFilesGenerator
        generator_ids = self._source_groups.setdefault(source_group, set())
        generator_ids.add(generator_id)
        generatedfile_registry.register(generator_id,
                SourceGroupFilesGenerator(source_group, generator_id))

    def unregister(self, generator_id, source_group):
        from .specs.sourcegroups import SourceGroupFilesGenerator
        generator_ids = self._source_groups.setdefault(source_group, set())
        if generator_id in generator_ids:
            generator_ids.remove(generator_id)
            generatedfile_registry.unregister(generator_id,
                    SourceGroupFilesGenerator(source_group, generator_id))

    def source_group_receiver(self, sender, source, signal, **kwargs):
        """
        Relay source group signals to the appropriate spec strategy.

        """
        from .files import GeneratedImageFile
        source_group = sender

        # Ignore signals from unregistered groups.
        if source_group not in self._source_groups:
            return

        specs = [generator_registry.get(id, source=source) for id in
                self._source_groups[source_group]]
        callback_name = self._signals[signal]

        for spec in specs:
            file = GeneratedImageFile(spec)
            call_strategy_method(spec, callback_name, file=file)


class GeneratedFileRegistry(object):
    """
    An object for registering generated files with image generators. The two are
    associated with each other via a string id. We do this (as opposed to
    associating them directly by, for example, putting a ``generatedfiles``
    attribute on image generators) so that image generators can be overridden
    without losing the associated files. That way, a distributable app can
    define its own generators without locking the users of the app into it.

    """

    def __init__(self):
        self._generatedfiles = {}

    def register(self, generator_id, generatedfiles):
        """
        Associates generated files with a generator id

        """
        if generatedfiles not in self._generatedfiles:
            self._generatedfiles[generatedfiles] = set()
        self._generatedfiles[generatedfiles].add(generator_id)

    def unregister(self, generator_id, generatedfiles):
        """
        Disassociates generated files with a generator id

        """
        try:
            self._generatedfiles[generatedfiles].remove(generator_id)
        except KeyError:
            pass

    def get(self, generator_id):
        for k, v in self._generatedfiles.items():
            if generator_id in v:
                for file in k():
                    yield file


class Register(object):
    """
    Register generators and generated files.

    """
    def generator(self, id, generator=None):
        if generator is None:
            # Return a decorator
            def decorator(cls):
                self.generator(id, cls)
                return cls
            return decorator

        generator_registry.register(id, generator)

    # iterable that returns kwargs or callable that returns iterable of kwargs
    def generatedfiles(self, generator_id, generatedfiles):
        generatedfile_registry.register(generator_id, generatedfiles)

    def source_group(self, generator_id, source_group):
        source_group_registry.register(generator_id, source_group)


class Unregister(object):
    """
    Unregister generators and generated files.

    """
    def generator(self, id, generator):
        generator_registry.unregister(id, generator)

    def generatedfiles(self, generator_id, generatedfiles):
        generatedfile_registry.unregister(generator_id, generatedfiles)

    def source_group(self, generator_id, source_group):
        source_group_registry.unregister(generator_id, source_group)


generator_registry = GeneratorRegistry()
generatedfile_registry = GeneratedFileRegistry()
source_group_registry = SourceGroupRegistry()
register = Register()
unregister = Unregister()
