"""
Tests for request-local state cache functionality.
"""
from unittest import mock
import pytest

from django.conf import settings

from imagekit.cachefiles import ImageCacheFile
from imagekit.cachefiles.backends import Simple, CachedFileBackend, CacheFileState
from imagekit.cachefiles.state import use_cachefile_state_cache, prefetch_cachefile_states

from .imagegenerators import TestSpec, ResizeTo1PixelSquare
from .utils import get_unique_image_file, clear_imagekit_cache


def test_get_state_uses_request_local_cache_without_hitting_django_cache():
    """
    Ensure get_state() consults request-local cache first and doesn't call
    Django cache.get() for pre-seeded keys.
    """
    clear_imagekit_cache()

    with get_unique_image_file() as source_file:
        spec = TestSpec(source=source_file)
        file = ImageCacheFile(spec)
        backend = file.cachefile_backend

        # Spy on cache.get
        cache_get = mock.patch.object(backend.cache, 'get')

        with cache_get as mock_get:
            # First call - should hit cache
            mock_get.return_value = CacheFileState.DOES_NOT_EXIST
            state1 = backend.get_state(file)
            assert state1 == CacheFileState.DOES_NOT_EXIST
            assert mock_get.call_count == 1

            # Now activate request-local cache and pre-seed it
            state_cache = {backend.get_key(file): CacheFileState.EXISTS}
            with use_cachefile_state_cache(state_cache):
                mock_get.reset_mock()
                # Should get state from request-local cache, not Django cache
                state2 = backend.get_state(file)
                assert state2 == CacheFileState.EXISTS
                assert mock_get.call_count == 0


def test_get_state_with_unknown_state_still_updates_request_local_cache():
    """
    Ensure get_state() with check_if_unknown=True stores newly discovered
    state in the request-local cache.
    """
    clear_imagekit_cache()

    with get_unique_image_file() as source_file:
        spec = TestSpec(source=source_file)
        file = ImageCacheFile(spec)
        backend = file.cachefile_backend

        state_cache = {}
        with use_cachefile_state_cache(state_cache):
            # First call with check_if_unknown=True (file doesn't exist yet)
            # This should call cache.get() (returns None), check storage,
            # and store DOES_NOT_EXIST in both Django cache and request-local cache
            state = backend.get_state(file)
            assert state == CacheFileState.DOES_NOT_EXIST

            # Verify request-local cache was updated
            key = backend.get_key(file)
            assert key in state_cache
            assert state_cache[key] == CacheFileState.DOES_NOT_EXIST


def test_prefetch_cachefile_states_uses_get_many_once_and_populates_mapping():
    """
    Ensure prefetch_cachefile_states() calls cache.get_many() once and
    populates the state_cache with both hits and misses.
    """
    clear_imagekit_cache()

    # Create multiple files with different specs to get unique cache keys
    files = []

    # Create 3 different specs with different sources
    for _ in range(3):
        with get_unique_image_file() as source_file:
            spec = TestSpec(source=source_file)
            file = ImageCacheFile(spec)
            files.append(file)

    backend = files[0].cachefile_backend

    # Prefetch states - use the actual backend cache
    state_cache = {}
    prefetch_cachefile_states(files, cache=backend.cache, state_cache=state_cache)

    # Verify state_cache was populated with all unique keys
    assert len(state_cache) == 3

    # All should be None (misses) since no states are in the cache
    for key, value in state_cache.items():
        assert value is None


def test_prefetch_uses_active_request_local_cache_when_none_provided():
    """
    Ensure prefetch_cachefile_states() uses active request-local cache
    when state_cache parameter is not provided.
    """
    clear_imagekit_cache()

    with get_unique_image_file() as source_file:
        spec = TestSpec(source=source_file)
        file = ImageCacheFile(spec)
        backend = file.cachefile_backend

        key = backend.get_key(file)

        with mock.patch.object(backend.cache, 'get_many') as mock_get_many:
            mock_get_many.return_value = {key: CacheFileState.EXISTS}

            # Activate request-local cache
            with use_cachefile_state_cache() as state_cache:
                prefetch_cachefile_states([file])

                # Verify active cache was populated
                assert key in state_cache
                assert state_cache[key] == CacheFileState.EXISTS


def test_prefetch_does_nothing_when_no_active_cache_and_none_provided():
    """
    Ensure prefetch_cachefile_states() is a no-op when no state_cache is
    provided and no active request-local cache exists.
    """
    clear_imagekit_cache()

    with get_unique_image_file() as source_file:
        spec = TestSpec(source=source_file)
        file = ImageCacheFile(spec)
        backend = file.cachefile_backend

        with mock.patch.object(backend.cache, 'get_many') as mock_get_many:
            prefetch_cachefile_states([file])

            # Should not call get_many since there's no cache to populate
            assert mock_get_many.call_count == 0


def test_set_state_updates_request_local_cache():
    """
    Ensure set_state() updates the active request-local cache (write-through).
    """
    clear_imagekit_cache()

    with get_unique_image_file() as source_file:
        spec = TestSpec(source=source_file)
        file = ImageCacheFile(spec)
        backend = file.cachefile_backend

        state_cache = {}
        with use_cachefile_state_cache(state_cache):
            # Set state
            backend.set_state(file, CacheFileState.GENERATING)

            # Verify request-local cache was updated
            key = backend.get_key(file)
            assert key in state_cache
            assert state_cache[key] == CacheFileState.GENERATING


def test_multiple_get_state_calls_only_hit_cache_once_after_prefetch():
    """
    Ensure that after prefetching, multiple get_state() calls don't hit
    the Django cache.
    """
    clear_imagekit_cache()

    # Create multiple files
    files = []
    with get_unique_image_file() as source_file:
        for i in range(5):
            spec = TestSpec(source=source_file)
            file = ImageCacheFile(spec)
            files.append(file)

    backend = files[0].cachefile_backend

    with mock.patch.object(backend.cache, 'get') as mock_get, \
         mock.patch.object(backend.cache, 'get_many') as mock_get_many:
        # Set up get_many to return all files as existing
        keys = [backend.get_key(f) for f in files]
        mock_get_many.return_value = {k: CacheFileState.EXISTS for k in keys}

        # Activate request-local cache and prefetch
        with use_cachefile_state_cache() as state_cache:
            prefetch_cachefile_states(files, state_cache=state_cache)

            # Mock get_many should have been called once
            assert mock_get_many.call_count == 1
            assert mock_get.call_count == 0

            # Now call get_state for each file multiple times
            for _ in range(3):
                for file in files:
                    state = backend.get_state(file)
                    assert state == CacheFileState.EXISTS

            # Verify no additional cache.get() calls
            assert mock_get.call_count == 0


def test_prefetch_groups_by_backend_cache_when_cache_not_provided():
    """
    Ensure prefetch_cachefile_states() uses each file's backend cache when
    no explicit cache is passed.

    This supports projects that mix cachefile backends (and potentially cache
    aliases).
    """
    clear_imagekit_cache()

    cache_a = mock.Mock()
    cache_b = mock.Mock()

    backend_a = CachedFileBackend()
    backend_b = CachedFileBackend()

    backend_a._cache = cache_a
    backend_b._cache = cache_b

    with get_unique_image_file() as source_file_a, get_unique_image_file() as source_file_b:
        spec_a = TestSpec(source=source_file_a)
        spec_b = TestSpec(source=source_file_b)

        file_a = ImageCacheFile(spec_a, cachefile_backend=backend_a)
        file_b = ImageCacheFile(spec_b, cachefile_backend=backend_b)

        key_a = backend_a.get_key(file_a)
        key_b = backend_b.get_key(file_b)

        cache_a.get_many.return_value = {key_a: CacheFileState.EXISTS}
        cache_b.get_many.return_value = {key_b: CacheFileState.GENERATING}

        state_cache = {}
        prefetch_cachefile_states([file_a, file_b], state_cache=state_cache)

        cache_a.get_many.assert_called_once_with({key_a})
        cache_b.get_many.assert_called_once_with({key_b})

        assert state_cache[key_a] == CacheFileState.EXISTS
        assert state_cache[key_b] == CacheFileState.GENERATING


def test_prefetch_uses_provided_cache_for_all_backends():
    """Ensure the `cache=` kwarg overrides per-backend caches."""
    clear_imagekit_cache()

    shared_cache = mock.Mock()

    cache_a = mock.Mock()
    cache_b = mock.Mock()

    backend_a = CachedFileBackend()
    backend_b = CachedFileBackend()

    backend_a._cache = cache_a
    backend_b._cache = cache_b

    with get_unique_image_file() as source_file_a, get_unique_image_file() as source_file_b:
        spec_a = TestSpec(source=source_file_a)
        spec_b = TestSpec(source=source_file_b)

        file_a = ImageCacheFile(spec_a, cachefile_backend=backend_a)
        file_b = ImageCacheFile(spec_b, cachefile_backend=backend_b)

        key_a = backend_a.get_key(file_a)
        key_b = backend_b.get_key(file_b)

        shared_cache.get_many.return_value = {
            key_a: CacheFileState.EXISTS,
            key_b: CacheFileState.EXISTS,
        }

        state_cache = {}
        prefetch_cachefile_states([file_a, file_b], cache=shared_cache, state_cache=state_cache)

        shared_cache.get_many.assert_called_once_with({key_a, key_b})
        assert cache_a.get_many.call_count == 0
        assert cache_b.get_many.call_count == 0

        assert state_cache[key_a] == CacheFileState.EXISTS
        assert state_cache[key_b] == CacheFileState.EXISTS


def test_use_cachefile_state_cache_creates_new_dict_if_none_provided():
    """
    Ensure use_cachefile_state_cache() creates a new dict if None is passed.
    """
    clear_imagekit_cache()

    with use_cachefile_state_cache() as state_cache:
        # Should get a dict
        assert isinstance(state_cache, dict)
        # Should be empty
        assert len(state_cache) == 0

        # Can add values
        state_cache['test_key'] = 'test_value'
        assert state_cache['test_key'] == 'test_value'

    # After context exit, the cache should no longer be active
    from imagekit.cachefiles.state import get_active_state_cache
    assert get_active_state_cache() is None
