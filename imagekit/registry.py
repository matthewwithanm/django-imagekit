from .exceptions import AlreadyRegistered, NotRegistered
from .signals import content_required, existence_required, source_saved
from .utils import autodiscover, call_strategy_method


class GeneratorRegistry:
    """
    An object for registering generators. This registry provides
    a convenient way for a distributable app to define default generators
    without locking the users of the app into it.

    """
    def __init__(self):
        self._generators = {}
        content_required.connect(self.content_required_receiver)
        existence_required.connect(self.existence_required_receiver)

    def register(self, id, generator):
        registered_generator = self._generators.get(id)
        if registered_generator and generator != self._generators[id]:
            raise AlreadyRegistered('The generator with id %s is'
                                    ' already registered' % id)
        self._generators[id] = generator

    def unregister(self, id):
        try:
            del self._generators[id]
        except KeyError:
            raise NotRegistered('The generator with id %s is not'
                                ' registered' % id)

    def get(self, id, **kwargs):
        autodiscover()

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
        autodiscover()
        return self._generators.keys()

    def content_required_receiver(self, sender, file, **kwargs):
        self._receive(file, 'on_content_required')

    def existence_required_receiver(self, sender, file, **kwargs):
        self._receive(file, 'on_existence_required')

    def _receive(self, file, callback):
        generator = file.generator

        # FIXME: I guess this means you can't register functions?
        if generator.__class__ in self._generators.values():
            # Only invoke the strategy method for registered generators.
            call_strategy_method(file, callback)


class SourceGroupRegistry:
    """
    The source group registry is responsible for listening to source_* signals
    on source groups, and relaying them to the image generated file strategies
    of the appropriate generators.

    In addition, registering a new source group also registers its generated
    files with that registry.

    """
    _signals = {
        source_saved: 'on_source_saved',
    }

    def __init__(self):
        self._source_groups = {}
        for signal in self._signals.keys():
            signal.connect(self.source_group_receiver)

    def register(self, generator_id, source_group):
        from .specs.sourcegroups import SourceGroupFilesGenerator
        generator_ids = self._source_groups.setdefault(source_group, set())
        generator_ids.add(generator_id)
        cachefile_registry.register(generator_id,
                SourceGroupFilesGenerator(source_group, generator_id))

    def unregister(self, generator_id, source_group):
        from .specs.sourcegroups import SourceGroupFilesGenerator
        generator_ids = self._source_groups.setdefault(source_group, set())
        if generator_id in generator_ids:
            generator_ids.remove(generator_id)
            cachefile_registry.unregister(generator_id,
                    SourceGroupFilesGenerator(source_group, generator_id))

    def source_group_receiver(self, sender, source, signal, **kwargs):
        """
        Relay source group signals to the appropriate spec strategy.

        """
        from .cachefiles import ImageCacheFile
        source_group = sender

        # Ignore signals from unregistered groups.
        if source_group not in self._source_groups:
            return

        specs = [generator_registry.get(id, source=source) for id in
                self._source_groups[source_group]]
        callback_name = self._signals[signal]

        for spec in specs:
            file = ImageCacheFile(spec)
            call_strategy_method(file, callback_name)


class CacheFileRegistry:
    """
    An object for registering generated files with image generators. The two are
    associated with each other via a string id. We do this (as opposed to
    associating them directly by, for example, putting a ``cachefiles``
    attribute on image generators) so that image generators can be overridden
    without losing the associated files. That way, a distributable app can
    define its own generators without locking the users of the app into it.

    """

    def __init__(self):
        self._cachefiles = {}

    def register(self, generator_id, cachefiles):
        """
        Associates generated files with a generator id

        """
        if cachefiles not in self._cachefiles:
            self._cachefiles[cachefiles] = set()
        self._cachefiles[cachefiles].add(generator_id)

    def unregister(self, generator_id, cachefiles):
        """
        Disassociates generated files with a generator id

        """
        try:
            self._cachefiles[cachefiles].remove(generator_id)
        except KeyError:
            pass

    def get(self, generator_id):
        for k, v in self._cachefiles.items():
            if generator_id in v:
                yield from k()


class Register:
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
    def cachefiles(self, generator_id, cachefiles):
        cachefile_registry.register(generator_id, cachefiles)

    def source_group(self, generator_id, source_group):
        source_group_registry.register(generator_id, source_group)


class Unregister:
    """
    Unregister generators and generated files.

    """
    def generator(self, id):
        generator_registry.unregister(id)

    def cachefiles(self, generator_id, cachefiles):
        cachefile_registry.unregister(generator_id, cachefiles)

    def source_group(self, generator_id, source_group):
        source_group_registry.unregister(generator_id, source_group)


generator_registry = GeneratorRegistry()
cachefile_registry = CacheFileRegistry()
source_group_registry = SourceGroupRegistry()
register = Register()
unregister = Unregister()
