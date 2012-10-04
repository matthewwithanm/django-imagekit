from .actions import validate_now, clear_now
from ..utils import get_singleton


class Pessimistic(object):
    """
    A caching strategy that validates the file every time it's accessed.

    """

    def on_access(self, file):
        validate_now(file)

    def on_source_delete(self, file):
        clear_now(file)

    def on_source_change(self, file):
        validate_now(file)


class Optimistic(object):
    """
    A caching strategy that validates when the source file changes and assumes
    that the cached file will persist.

    """

    def on_source_create(self, file):
        validate_now(file)

    def on_source_delete(self, file):
        clear_now(file)

    def on_source_change(self, file):
        validate_now(file)


class DictStrategy(object):
    def __init__(self, callbacks):
        for k, v in callbacks.items():
            setattr(self, k, v)


class StrategyWrapper(object):
    def __init__(self, strategy):
        if isinstance(strategy, basestring):
            strategy = get_singleton(strategy, 'image cache strategy')
        elif isinstance(strategy, dict):
            strategy = DictStrategy(strategy)
        elif callable(strategy):
            strategy = strategy()
        self._wrapped = strategy

    def invoke_callback(self, name, *args, **kwargs):
        func = getattr(self._wrapped, 'on_%s' % name, None)
        if func:
            func(*args, **kwargs)
