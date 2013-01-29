from django.utils.functional import LazyObject
from .actions import validate_now, clear_now
from ..utils import get_singleton


class JustInTime(object):
    """
    A caching strategy that validates the file right before it's needed.

    """

    def before_access(self, file):
        validate_now(file)


class Optimistic(object):
    """
    A caching strategy that acts immediately when the cacheable file changes
    and assumes that the cache files will not be removed (i.e. doesn't
    revalidate on access).

    """

    def on_source_created(self, file):
        validate_now(file)

    def on_source_deleted(self, file):
        clear_now(file)

    def on_source_changed(self, file):
        validate_now(file)


class DictStrategy(object):
    def __init__(self, callbacks):
        for k, v in callbacks.items():
            setattr(self, k, v)


class StrategyWrapper(LazyObject):
    def __init__(self, strategy):
        if isinstance(strategy, basestring):
            strategy = get_singleton(strategy, 'image cache strategy')
        elif isinstance(strategy, dict):
            strategy = DictStrategy(strategy)
        elif callable(strategy):
            strategy = strategy()
        self._wrapped = strategy

    def __getstate__(self):
        return {'_wrapped': self._wrapped}

    def __setstate__(self, state):
        self._wrapped = state['_wrapped']

    def __unicode__(self):
        return unicode(self._wrapped)

    def __str__(self):
        return str(self._wrapped)
