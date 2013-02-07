from django.utils.functional import LazyObject
from ..utils import get_singleton


class JustInTime(object):
    """
    A strategy that ensures the file exists right before it's needed.

    """

    def before_access(self, file):
        file.generate()


class Optimistic(object):
    """
    A strategy that acts immediately when the source file changes and assumes
    that the cache files will not be removed (i.e. it doesn't ensure the
    cache file exists when it's accessed).

    """

    def on_source_created(self, file):
        file.generate()

    def on_source_changed(self, file):
        file.generate()


class DictStrategy(object):
    def __init__(self, callbacks):
        for k, v in callbacks.items():
            setattr(self, k, v)


class StrategyWrapper(LazyObject):
    def __init__(self, strategy):
        if isinstance(strategy, basestring):
            strategy = get_singleton(strategy, 'cache file strategy')
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
