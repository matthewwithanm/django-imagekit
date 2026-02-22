"""
Request-local state cache for ImageKit cachefiles to reduce cache lookups.

This module provides an optional request-local in-memory state cache that can
be used to batch prefetch cache file states, reducing round trips to the Django
cache backend.
"""
from contextlib import contextmanager
from contextvars import ContextVar

# ContextVar for storing the active state cache (a dict-like mapping) for the
# current execution context.
_active_state_cache: ContextVar = ContextVar('_active_state_cache', default=None)


@contextmanager
def use_cachefile_state_cache(state_cache=None):
    """
    Context manager to activate a request-local state cache.

    Usage::

        from imagekit.cachefiles.state import use_cachefile_state_cache, prefetch_cachefile_states

        state_cache = {}
        with use_cachefile_state_cache(state_cache):
            prefetch_cachefile_states(thumbs, state_cache=state_cache)
            # ... render template with thumbs ...

    :param state_cache: A dict-like mapping to use as the cache.
        If None, a new empty dict will be created.
    """
    if state_cache is None:
        state_cache = {}

    token = _active_state_cache.set(state_cache)
    try:
        yield state_cache
    finally:
        _active_state_cache.reset(token)


def get_active_state_cache():
    """
    Get the active state cache for the current context, if any.

    :return: The active dict-like mapping, or None if no cache is active.
    """
    return _active_state_cache.get(None)


def prefetch_cachefile_states(files, *, state_cache=None, cache=None):
    """
    Prefetch cache file states using cache.get_many().

    This function computes cache keys for the given files and fetches their
    states in as few cache.get_many() calls as possible. The results are stored
    in the provided state_cache (or the active request-local cache if not
    provided).

    Example usage in a view::

        from imagekit.cachefiles.state import use_cachefile_state_cache, prefetch_cachefile_states

        def gallery(request):
            images = list(Image.objects.filter(...))
            thumbs = [img.thumbnail for img in images]

            state_cache = {}
            with use_cachefile_state_cache(state_cache):
                prefetch_cachefile_states(thumbs, state_cache=state_cache)
                return render(request, "gallery.html", {"images": images})

    :param files: Iterable of ImageCacheFile objects to prefetch states for.
    :param state_cache: Optional dict-like mapping to populate. If None,
        the active request-local cache will be used (if any).
    :param cache: Optional Django cache instance. If provided, all lookups
        will use this cache. If None, each file's cachefile backend will
        determine which cache to read from.
    """
    from .backends import CachedFileBackend

    if state_cache is None:
        state_cache = get_active_state_cache()
        if state_cache is None:
            return

    # Group keys by the Django cache object used for the lookup.
    keys_by_cache = {}

    for f in files:
        backend = getattr(f, 'cachefile_backend', None)
        if not isinstance(backend, CachedFileBackend):
            continue

        key = backend.get_key(f)

        backend_cache = cache or backend.cache
        keys_by_cache.setdefault(backend_cache, set()).add(key)

    if not keys_by_cache:
        return

    for backend_cache, keys in keys_by_cache.items():
        states = backend_cache.get_many(keys)

        # Store hits in state_cache
        for key, state in states.items():
            state_cache[key] = state

        # Also record misses so later checks don't fall back to cache.get()
        for key in keys:
            if key not in states:
                state_cache[key] = None
