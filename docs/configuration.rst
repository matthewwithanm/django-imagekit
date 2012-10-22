.. _settings:

Configuration
=============


Settings
--------

.. currentmodule:: django.conf.settings


.. attribute:: IMAGEKIT_CACHE_DIR

    :default: ``'CACHE/images'``

    The directory to which image files will be cached.


.. attribute:: IMAGEKIT_DEFAULT_FILE_STORAGE

    :default: ``None``

    The qualified class name of a Django storage backend to use to save the
    cached images. If no value is provided for ``IMAGEKIT_DEFAULT_FILE_STORAGE``,
    and none is specified by the spec definition, the storage of the source file
    will be used.


.. attribute:: IMAGEKIT_DEFAULT_IMAGE_CACHE_BACKEND

    :default: ``'imagekit.imagecache.backends.Simple'``

    Specifies the class that will be used to validate cached image files.


.. attribute:: IMAGEKIT_DEFAULT_IMAGE_CACHE_STRATEGY

    :default: ``'imagekit.imagecache.strategies.JustInTime'``

    The class responsible for specifying how and when cache files are
    generated.


.. attribute:: IMAGEKIT_CACHE_BACKEND

    :default: If ``DEBUG`` is ``True``, ``'django.core.cache.backends.dummy.DummyCache'``.
    Otherwise, ``'default'``.

    The Django cache backend to be used to store information like the state of
    cached images (i.e. validated or not).


.. attribute:: IMAGEKIT_CACHE_PREFIX

    :default: ``'imagekit:'``

    A cache prefix to be used when values are stored in ``IMAGEKIT_CACHE_BACKEND``


Optimization
------------

Not surprisingly, the trick to getting the most out of ImageKit is to reduce the
number of I/O operations. This can be especially important if your source files
aren't stored on the same server as the application.


Image Cache Strategies
^^^^^^^^^^^^^^^^^^^^^^

An important way of reducing the number of I/O operations that ImageKit makes is
by controlling when cached images are validated. This is done through "image
cache strategies"—objects that associate signals dispatched on the source file
with file actions. The default image cache strategy is
``'imagekit.imagecache.strategies.JustInTime'``; it looks like this:

.. code-block:: python

    class JustInTime(object):
        def before_access(self, file):
            validate_now(file)

When this strategy is used, the cache file is validated only immediately before
it's required—for example, when you access its url, path, or contents. This
strategy is exceedingly safe: by guaranteeing the presence of the file before
accessing it, you run no risk of it not being there. However, this strategy can
also be costly: verifying the existence of the cache file every time you access
it can be slow—particularly if the file is on another server. For this reason,
ImageKit provides another strategy: ``imagekit.imagecache.strategies.Optimistic``.
Unlike the just-in-time strategy, it does not validate the cache file when it's
accessed, but rather only when the soure file is created or changed. Later, when
the cache file is accessed, it is presumed to still be present.

If neither of these strategies suits your application, you can create your own
strategy class. For example, you may wish to validate the file immediately when
it's accessed, but schedule validation using Celery when the source file is
saved or changed:

.. code-block:: python

    from imagekit.imagecache.actions import validate_now, deferred_validate

    class CustomImageCacheStrategy(object):

        def before_access(self, file):
            validate_now(file)

        def on_source_created(self, file):
            deferred_validate(file)

        def on_source_changed(self, file):
            deferred_validate(file)

To use this cache strategy, you need only set the ``IMAGEKIT_DEFAULT_IMAGE_CACHE_STRATEGY``
setting, or set the ``image_cache_strategy`` attribute of your image spec.


Django Cache Backends
^^^^^^^^^^^^^^^^^^^^^

In the "Image Cache Strategies" section above, we said that the just-in-time
strategy verifies the existence of the cache file every time you access
it, however, that's not exactly true. Cache files are actually validated using
image cache backends, and the default (``imagekit.imagecache.backends.Simple``)
memoizes the cache state (valid or invalid) using Django's cache framework. By
default, ImageKit will use a dummy cache backend when your project is in debug
mode (``DEBUG = True``), and the "default" cache (from your ``CACHES`` setting)
when ``DEBUG`` is ``False``. Since other parts of your project may have
different cacheing needs, though, ImageKit has an ``IMAGEKIT_CACHE_BACKEND``
setting, which allows you to specify a different cache.

In most cases, you won't be deleting you cached files once they're created, so
using a cache with a large timeout is a great way to optimize your site. Using
a cache that never expires would essentially negate the cost of the just-in-time
strategy, giving you the benefit of generating images on demand without the cost
of unnecessary future filesystem checks.
