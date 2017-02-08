Caching
*******


Default Backend Workflow
================


``ImageSpec``
-------------

At the heart of ImageKit are image generators. These are classes with a
``generate()`` method which returns an image file. An image spec is a type of
image generator. The thing that makes specs special is that they accept a source
image. So an image spec is just an image generator that makes an image from some
other image.


``ImageCacheFile``
------------------

However, an image spec by itself would be vastly inefficient. Every time an
an image was accessed in some way, it would have be regenerated and saved.
Most of the time, you want to re-use a previously generated image, based on the
input image and spec, instead of generating a new one. That's where
``ImageCacheFile`` comes in. ``ImageCacheFile`` is a File-like object that
wraps an image generator. They look and feel just like regular file
objects, but they've got a little trick up their sleeve: they represent files
that may not actually exist!


Cache File Strategy
-------------------

Each ``ImageCacheFile`` has a cache file strategy, which abstracts away when
image is actually generated. It can implement the following three methods:

* ``on_content_required`` - called by ``ImageCacheFile`` when it requires the
  contents of the generated image. For example, when you call ``read()`` or
  try to access information contained in the file.
* ``on_existence_required`` - called by ``ImageCacheFile`` when it requires the
  generated image to exist but may not be concerned with its contents. For
  example, when you access its ``url`` or ``path`` attribute.
* ``on_source_saved`` - called when the source of a spec is saved

The default strategy only defines the first two of these, as follows:

.. code-block:: python

    class JustInTime(object):
        def on_content_required(self, file):
            file.generate()

        def on_existence_required(self, file):
            file.generate()


Cache File Backend
------------------

The ``generate`` method on the ``ImageCacheFile`` is further delegated to the
cache file backend, which abstracts away how an image is generated.

The cache file backend defaults to the setting
``IMAGEKIT_DEFAULT_CACHEFILE_BACKEND`` and can be set explicitly on a spec with
the ``cachefile_backend`` attribute.

The default works like this:

* Checks the file storage to see if a file exists
    * If not, caches that information for 5 seconds
    * If it does, caches that information in the ``IMAGEKIT_CACHE_BACKEND``

If file doesn't exist, generates it immediately and synchronously


That pretty much covers the architecture of the caching layer, and its default
behavior. I like the default behavior. When will an image be regenerated?
Whenever it needs to be! When will your storage backend get hit? Depending on
your ``IMAGEKIT_CACHE_BACKEND`` settings, as little as twice per file (once for the
existence check and once to save the generated file). What if you want to change
a spec? The generated file name (which is used as part of the cache keys) vary
with the source file name and spec attributes, so if you change any of those, a
new file will be generated. The default behavior is easy!

.. note::

    Like regular Django ImageFields, IK doesn't currently cache width and height
    values, so accessing those will always result in a read. That will probably
    change soon though.


Optimizing
==========

There are several ways to improve the performance (reduce I/O operations) of
ImageKit. Each has its own pros and cons.


Caching Data About Generated Files
----------------------------------

Generally, once a file is generated, you will never be removing it, so by
default ImageKit will use default cache to cache the state of generated
files "forever" (or only 5 minutes when ``DEBUG = True``).

The time for which ImageKit will cache state is configured with
``IMAGEKIT_CACHE_TIMEOUT``. If set to ``None`` this means "never expire"
(default when ``DEBUG = False``). You can reduce this timeout if you want
or set it to some numeric value in seconds if your cache backend behaves
differently and for example do not cache values if timeout is ``None``.

If you clear your cache durring deployment or some other reason probably
you do not want to lose the cache for generated images especcialy if you
are using some slow remote storage (like Amazon S3). Then you can configure
seprate cache (for example redis) in your ``CACHES`` config and tell ImageKit
to use it instead of the default cache by setting ``IMAGEKIT_CACHE_BACKEND``.


Pre-Generating Images
---------------------

The default cache file backend generates images immediately and synchronously.
If you don't do anything special, that will be when they are first requested—as
part of request-response cycle. This means that the first visitor to your page
will have to wait for the file to be created before they see any HTML.

This can be mitigated, though, by simply generating the images ahead of time, by
running the ``generateimages`` management command.

.. note::

    If using with template tags, be sure to read :ref:`source-groups`.


Deferring Image Generation
--------------------------

As mentioned above, image generation is normally done synchronously. through
the default cache file backend. However, you can also take advantage of
deferred generation. In order to do this, you'll need to do two things:

1) install `celery`__ (or `django-celery`__ if you are bound to Celery<3.1)
2) tell ImageKit to use the async cachefile backend.
   To do this for all specs, set the ``IMAGEKIT_DEFAULT_CACHEFILE_BACKEND`` in
   your settings

.. code-block:: python

    IMAGEKIT_DEFAULT_CACHEFILE_BACKEND = 'imagekit.cachefiles.backends.Async'

Images will now be generated asynchronously. But watch out! Asynchrounous
generation means you'll have to account for images that haven't been generated
yet. You can do this by checking the truthiness of your files; if an image
hasn't been generated, it will be falsy:

.. code-block:: html

    {% if not profile.avatar_thumbnail %}
        <img src="/path/to/placeholder.jpg" />
    {% else %}
        <img src="{{ profile.avatar_thumbnail.url }}" />
    {% endif %}

Or, in Python:

.. code-block:: python

    profile = Profile.objects.all()[0]
    if profile.avatar_thumbnail:
        url = profile.avatar_thumbnail.url
    else:
        url = '/path/to/placeholder.jpg'

.. note::

    If you are using an "async" backend in combination with the "optimistic"
    cache file strategy (see `Removing Safeguards`_ below), checking for
    thruthiness as described above will not work. The "optimistic" backend is
    very optimistic so to say, and removes the check. Create and use the
    following strategy to a) have images only created on save, and b) retain
    the ability to check whether the images have already been created::

        class ImagekitOnSaveStrategy(object):
            def on_source_saved(self, file):
                file.generate()



__ https://pypi.python.org/pypi/django-celery
__ http://www.celeryproject.org


Removing Safeguards
-------------------

Even with pre-generating images, ImageKit will still try to ensure that your
image exists when you access it by default. This is for your benefit: if you
forget to generate your images, ImageKit will see that and generate it for you.
If the state of the file is cached (see above), this is a pretty cheap
operation. However, if the state isn't cached, ImageKit will need to query the
storage backend.

For those who aren't willing to accept that cost (and who never want ImageKit
to generate images in the request-responce cycle), there's the "optimistic"
cache file strategy. This strategy only generates a new image when a spec's
source image is created or changed. Unlike with the "just in time" strategy,
accessing the file won't cause it to be generated, ImageKit will just assume
that it already exists.

To use this cache file strategy for all specs, set the
``IMAGEKIT_DEFAULT_CACHEFILE_STRATEGY`` in your settings:

.. code-block:: python

    IMAGEKIT_DEFAULT_CACHEFILE_STRATEGY = 'imagekit.cachefiles.strategies.Optimistic'

If you have specs that :ref:`change based on attributes of the source
<dynamic-specs>`, that's not going to cut it, though; the file will also need to
be generated when those attributes change. Likewise, image generators that don't
have sources (i.e. generators that aren't specs) won't cause files to be
generated automatically when using the optimistic strategy. (ImageKit can't know
when those need to be generated, if not on access.) In both cases, you'll have
to trigger the file generation yourself—either by generating the file in code
when necessary, or by periodically running the ``generateimages`` management
command. Luckily, ImageKit makes this pretty easy:

.. code-block:: python

    from imagekit.cachefiles import LazyImageCacheFile

    file = LazyImageCacheFile('myapp:profile:avatar_thumbnail', source=source_file)
    file.generate()

One final situation in which images won't be generated automatically when using
the optimistic strategy is when you use a spec with a source that hasn't been
registered with it. Unlike the previous two examples, this situation cannot be
rectified by running the ``generateimages`` management command, for the simple
reason that the command has no way of knowing it needs to generate a file for
that spec from that source. Typically, this situation would arise when using the
template tags. Unlike ImageSpecFields, which automatically register all the
possible source images with the spec you define, the template tags
("generateimage" and "thumbnail") let you use any spec with any source.
Therefore, in order to generate the appropriate files using the
``generateimages`` management command, you'll need to first register a source
group that represents all of the sources you wish to use with the corresponding
specs. See :ref:`source-groups` for more information.
