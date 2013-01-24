from .exceptions import AlreadyRegistered, NotRegistered
from .signals import (before_access, cacheable_created, cacheable_changed,
                       cacheable_deleted)


class GeneratorRegistry(object):
    """
    An object for registering generators. This registry provides
    a convenient way for a distributable app to define default generators
    without locking the users of the app into it.

    """
    def __init__(self):
        self._generators = {}

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


class CacheableRegistry(object):
    """
    An object for registering cacheables with generators. The two are
    associated with each other via a string id. We do this (as opposed to
    associating them directly by, for example, putting a ``cacheables``
    attribute on generators) so that generators can be overridden without
    losing the associated cacheables. That way, a distributable app can define
    its own generators without locking the users of the app into it.

    """

    _signals = [
        cacheable_created,
        cacheable_changed,
        cacheable_deleted,
    ]

    def __init__(self):
        self._cacheables = {}
        for signal in self._signals:
            signal.connect(self.cacheable_receiver)
        before_access.connect(self.before_access_receiver)

    def register(self, generator_id, cacheables):
        """
        Associates cacheables with a generator id

        """
        for cacheable in cacheables:
            if cacheable not in self._cacheables:
                self._cacheables[cacheable] = set()
            self._cacheables[cacheable].add(generator_id)

    def unregister(self, generator_id, cacheables):
        """
        Disassociates cacheables with a generator id

        """
        for cacheable in cacheables:
            try:
                self._cacheables[cacheable].remove(generator_id)
            except KeyError:
                continue

    def get(self, generator_id):
        return [cacheable for cacheable in self._cacheables
                if generator_id in self._cacheables[cacheable]]

    def before_access_receiver(self, sender, generator, cacheable, **kwargs):
        generator.image_cache_strategy.invoke_callback('before_access', cacheable)

    def cacheable_receiver(self, sender, cacheable, signal, info, **kwargs):
        """
        Redirects signals dispatched on cacheables
        to the appropriate generators.

        """
        cacheable = sender
        if cacheable not in self._cacheables:
            return

        for generator in (generator_registry.get(id, cacheable=cacheable, **info)
                     for id in self._cacheables[cacheable]):
            event_name = {
                cacheable_created: 'cacheable_created',
                cacheable_changed: 'cacheable_changed',
                cacheable_deleted: 'cacheable_deleted',
            }
            generator._handle_cacheable_event(event_name, cacheable)


class Register(object):
    """
    Register generators and cacheables.

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
    def cacheables(self, generator_id, cacheables):
        if callable(cacheables):
            cacheables = cacheables()
        cacheable_registry.register(generator_id, cacheables)


class Unregister(object):
    """
    Unregister generators and cacheables.

    """
    def generator(self, id, generator):
        generator_registry.unregister(id, generator)

    def cacheables(self, generator_id, cacheables):
        if callable(cacheables):
            cacheables = cacheables()
        cacheable_registry.unregister(generator_id, cacheables)


generator_registry = GeneratorRegistry()
cacheable_registry = CacheableRegistry()
register = Register()
unregister = Unregister()
