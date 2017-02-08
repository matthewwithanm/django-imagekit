.. _settings:

Configuration
=============


Settings
--------

.. currentmodule:: django.conf.settings


.. attribute:: IMAGEKIT_CACHEFILE_DIR

    :default: ``'CACHE/images'``

    The directory to which image files will be cached.


.. attribute:: IMAGEKIT_DEFAULT_FILE_STORAGE

    :default: ``None``

    The qualified class name of a Django storage backend to use to save the
    cached images. If no value is provided for ``IMAGEKIT_DEFAULT_FILE_STORAGE``,
    and none is specified by the spec definition, `your default file storage`__
    will be used.


.. attribute:: IMAGEKIT_DEFAULT_CACHEFILE_BACKEND

    :default: ``'imagekit.cachefiles.backends.Simple'``

    Specifies the class that will be used to validate cached image files.


.. attribute:: IMAGEKIT_DEFAULT_CACHEFILE_STRATEGY

    :default: ``'imagekit.cachefiles.strategies.JustInTime'``

    The class responsible for specifying how and when cache files are
    generated.


.. attribute:: IMAGEKIT_CACHE_BACKEND

    :default:  ``'default'``

    The Django cache backend alias to retrieve the shared cache instance defined
    in your settings, as described in the `Django cache section`_.

    The cache is then used to store information like the state of cached
    images (i.e. validated or not).

.. _`Django cache section`: https://docs.djangoproject.com/en/1.8/topics/cache/#accessing-the-cache


.. attribute:: IMAGEKIT_CACHE_TIMEOUT

    :default: ``None``

    Use when you need to override the timeout used to cache file state.
    By default it is "cache forever".
    It's highly recommended that you use a very high timeout.


.. attribute:: IMAGEKIT_CACHE_PREFIX

    :default: ``'imagekit:'``

    A cache prefix to be used when values are stored in ``IMAGEKIT_CACHE_BACKEND``


.. attribute:: IMAGEKIT_CACHEFILE_NAMER

    :default: ``'imagekit.cachefiles.namers.hash'``

    A function responsible for generating file names for non-spec cache files.


.. attribute:: IMAGEKIT_SPEC_CACHEFILE_NAMER

    :default: ``'imagekit.cachefiles.namers.source_name_as_path'``

    A function responsible for generating file names for cache files that
    correspond to image specs. Since you will likely want to base the name of
    your cache files on the name of the source, this extra setting is provided.


__ https://docs.djangoproject.com/en/dev/ref/settings/#default-file-storage
