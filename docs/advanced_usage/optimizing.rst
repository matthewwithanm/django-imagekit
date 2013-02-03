Unlike Django's ImageFields, ImageKit's ImageSpecFields and template tags don't
persist any data in the database. Therefore, in order to know whether an image
file needs to be generated, ImageKit needs to check if the file already exists
(using the appropriate file storage object`__). The object responsible for
performing these checks is called a *generated file backend*.


Cache!
------

By default, ImageKit checks for the existence of a generated file every time you
attempt to use the file and, if it doesn't exist, creates it synchronously. This
is a very safe behavior because it ensures that your ImageKit-generated images
are always available. However, that's a lot of checking with storage and those
kinds of operations can be slow—especially if you're using a remote storage—so
you'll want to try to avoid them as much as possible.

Luckily, the default generated file backend makes use of Django's caching
abilities to mitigate the number of checks it actually has to do; it will use
the cache specified by the ``IMAGEKIT_CACHE_BACKEND`` to save the state of the
generated file. If your Django project is running in debug mode
(``settings.DEBUG`` is true), this will be a dummy cache by default. Otherwise,
it will use your project's default cache.

In normal operation, your generated files will never be deleted; once they're
created, they'll stay created. So the simplest optimization you can make is to
set your ``IMAGEKIT_CACHE_BACKEND`` to a cache with a very long, or infinite,
timeout.


Even More Advanced
------------------

For many applications—particularly those using local storage for generated image
files—a cache with a long timeout is all the optimization you'll need. However,
there may be times when that simply doesn't cut it. In these cases, you'll want
to change when the generation is actually done.

The objects responsible for specifying when generated files are created are
called *generated file strategies*. The default strategy can be set using the
``IMAGEKIT_DEFAULT_GENERATEDFILE_STRATEGY`` setting, and its default value is
`'imagekit.generatedfiles.strategies.JustInTime'`. As we've already seen above,
the "just in time" strategy determines whether a file needs to be generated each
time it's accessed and, if it does, generates it synchronously.



__ https://docs.djangoproject.com/en/dev/ref/files/storage/
