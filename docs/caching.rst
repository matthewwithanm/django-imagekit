Caching
*******

Default Backend Workflow
================

``ImageSpec``
-------------

At the heart of ImageKit are image generators. These are callables which return
a modified image. An image spec is a type of image generator. The thing that
makes specs special is that they accept a source image. So an image spec is
just an image generator that makes an image from some other image.

``ImageCacheFile``
------------------

However, an image spec by itself would be vastly inefficient. Every time an
an image was accessed in some way, it would have be regenerated at saved.
Most of the time, you want to re-use a previously generated image, based on the
inpurt image and spec, instead generating a new one. That's where
``ImageCacheFile`` comes in. ``ImageCacheFile`` is a File-like object that
is returned from an image generator. They look and feel just like regular file
objects, but they've got a little trick up their sleeve: they represent files
that may not actually exist!

Cache File Strategy
-------------------
Each ``ImageCacheFile`` has a cache file strategy, which abstracts away when
image is actually generated. It implenents four methods.

* ``before_access`` - called by ``ImageCacheFile`` when you access its url,
  width, or height attribute.
* ``on_source_created`` - called when the source of a spec is created
* ``on_source_changed`` - called when the source of a spec is changed
* ``on_source_deleted`` - called when the source of a spec is deleted

The default strategy only defines the first of these, as follows:

.. code-block:: python

    class JustInTime(object):
        def before_access(self, file):
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

If file doesn't exsit, generates it immediately and synchronously


That pretty much covers the architecture of the caching layer, and its default
behavior. I like the default behavior. When will an image be regenerated?
Whenever it needs to be! When will your storage backend get hit? Depending on
our IMAGEKIT_CACHE_BACKEND settings, as little as twice per file (once for the
existence check and once to save the generated file).
(Actually, like regular Django ImageFields, IK never caches width and height
so those will always result in a read. That will probably change soon though.)
What if you want to change a spec? The generated file name (which is used as
part of the cache keys) vary with the source file name and spec attributes,
so if you change any of those, a new file will be generated. The default
behavior is easy!



Deferring Image Generation
==========================
As mentioned above, image generation is normally done synchronously. through
the default cache file backend. However, you can also take advantage of
deferred generation. In order to do this, you'll need to do two things:

1) install `django-celery`__
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


__ https://pypi.python.org/pypi/django-celery


Pre-Generating Images
=====================

The default behavior generates images "immediately and synchronously". They are
generated as part of the request-response cycle, which slows down the request.

This can be mitigated by generating the images generating the images outside of
a request. This can be done by running the ``generateimages``

.. note::

    If using with template tags, be sure to read :ref:`source-groups`.


Minimizing Storage Backend Access
=================================
However even with pre-generating images, the storage backend still has to be
queried to see if the file exists every time it is accessed. If you never
want ImageKit to generate images in the request-responce cycle, then it never
has to check if the image exists. The other cache file strategy only generates
a new image when their source image is created or changed.

To use this cache file strategy for all specs, set the
``IMAGEKIT_DEFAULT_CACHEFILE_STRATEGY`` in your settings

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
