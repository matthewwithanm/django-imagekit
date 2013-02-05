Unlike Django's ImageFields, ImageKit's ImageSpecFields and template tags don't
persist any data in the database. Therefore, in order to know whether an image
file needs to be generated, ImageKit needs to check if the file already exists
(using the appropriate file storage object`__). The object responsible for
performing these checks is called a *cache file backend*.


Cache!
------

By default, ImageKit checks for the existence of a cache file every time you
attempt to use the file and, if it doesn't exist, creates it synchronously. This
is a very safe behavior because it ensures that your ImageKit-generated images
are always available. However, that's a lot of checking with storage and those
kinds of operations can be slow—especially if you're using a remote storage—so
you'll want to try to avoid them as much as possible.

Luckily, the default cache file backend makes use of Django's caching
abilities to mitigate the number of checks it actually has to do; it will use
the cache specified by the ``IMAGEKIT_CACHE_BACKEND`` to save the state of the
generated file. If your Django project is running in debug mode
(``settings.DEBUG`` is true), this will be a dummy cache by default. Otherwise,
it will use your project's default cache.

In normal operation, your cache files will never be deleted; once they're
created, they'll stay created. So the simplest optimization you can make is to
set your ``IMAGEKIT_CACHE_BACKEND`` to a cache with a very long, or infinite,
timeout.


Even More Advanced
------------------

For many applications—particularly those using local storage for generated image
files—a cache with a long timeout is all the optimization you'll need. However,
there may be times when that simply doesn't cut it. In these cases, you'll want
to change when the generation is actually done.

The objects responsible for specifying when cache files are created are
called *cache file strategies*. The default strategy can be set using the
``IMAGEKIT_DEFAULT_CACHEFILE_STRATEGY`` setting, and its default value is
`'imagekit.cachefiles.strategies.JustInTime'`. As we've already seen above,
the "just in time" strategy determines whether a file needs to be generated each
time it's accessed and, if it does, generates it synchronously (that is, as part
of the request-response cycle).

Another strategy is to simply assume the file exists. This requires the fewest
number of checks (zero!), so we don't have to worry about expensive IO. The
strategy that takes this approach is
``imagekit.cachefiles.strategies.Optimistic``. In order to use this
strategy, either set the ``IMAGEKIT_DEFAULT_CACHEFILE_STRATEGY`` setting or,
to use it on a per-generator basis, set the ``cachefile_strategy`` attribute
of your spec or generator. Avoiding checking for file existence can be a real
boon to performance, but it also means that ImageKit has no way to know when a
file needs to be generated—well, at least not all the time.

With image specs, we can know at least some of the times that a new file needs
to be generated: whenever the source image is created or changed. For this
reason, the optimistic strategy defines callbacks for these events. Every
`source registered with ImageKit`__ will automatically cause its specs' files to
be generated when it is created or changed.

.. note::

    In order to understand source registration, read :ref:`source-groups`

If you have specs that `change based on attributes of the source`__, that's not
going to cut it, though; the file will also need to be generated when those
attributes change. Likewise, image generators that don't have sources (i.e.
generators that aren't specs) won't cause files to be generated automatically
when using the optimistic strategy. (ImageKit can't know when those need to be
generated, if not on access.) In both cases, you'll have to trigger the file
generation yourself—either by generating the file in code when necessary, or by
periodically running the ``generateimages`` management command. Luckily,
ImageKit makes this pretty easy:

.. code-block:: python

    from imagekit.cachefiles import LazyGeneratedImageFile

    file = LazyGeneratedImageFile('myapp:profile:avatar_thumbnail', source=source_file)
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


__ https://docs.djangoproject.com/en/dev/ref/files/storage/
__
__
