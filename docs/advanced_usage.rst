Advanced Usage
**************


Models
======


The ``ImageSpecField`` Shorthand Syntax
---------------------------------------

If you've read the README, you already know what an ``ImageSpecField`` is and
the basics of defining one:

.. code-block:: python

    from django.db import models
    from imagekit.models import ImageSpecField
    from imagekit.processors import ResizeToFill

    class Profile(models.Model):
        avatar = models.ImageField(upload_to='avatars')
        avatar_thumbnail = ImageSpecField(source='avatar',
                                          processors=[ResizeToFill(100, 50)],
                                          format='JPEG',
                                          options={'quality': 60})

This will create an ``avatar_thumbnail`` field which is a resized version of the
image stored in the ``avatar`` image field. But this is actually just shorthand
for creating an ``ImageSpec``, registering it, and associating it with an
``ImageSpecField``:

.. code-block:: python

    from django.db import models
    from imagekit import ImageSpec, register
    from imagekit.models import ImageSpecField
    from imagekit.processors import ResizeToFill

    class AvatarThumbnail(ImageSpec):
        processors = [ResizeToFill(100, 50)]
        format = 'JPEG'
        options = {'quality': 60}

    register.generator('myapp:profile:avatar_thumbnail', AvatarThumbnail)

    class Profile(models.Model):
        avatar = models.ImageField(upload_to='avatars')
        avatar_thumbnail = ImageSpecField(source='avatar',
                                          spec_id='myapp:profile:avatar_thumbnail')

Obviously, the shorthand version is a lot, well…shorter. So why would you ever
want to go through the trouble of using the long form? The answer is that the
long form—creating an image spec class and registering it—gives you a lot more
power over the generated image.


.. _dynamic-specs:

Specs That Change
-----------------

As you'll remember from the README, an image spec is just a type of image
generator that generates a new image from a source image. How does the image
spec get access to the source image? Simple! It's passed to the constructor as
a keyword argument and stored as an attribute of the spec. Normally, we don't
have to concern ourselves with this; the ``ImageSpec`` knows what to do with the
source image and we're happy to let it do its thing. However, having access to
the source image in our spec class can be very useful…

Often, when using an ``ImageSpecField``, you may want the spec to vary based on
properties of a model. (For example, you might want to store image dimensions on
the model and then use them to generate your thumbnail.) Now that we know how to
access the source image from our spec, it's a simple matter to extract its model
and use it to create our processors list. In fact, ImageKit includes a utility
for getting this information.

.. code-block:: python
    :emphasize-lines: 11-14

    from django.db import models
    from imagekit import ImageSpec, register
    from imagekit.models import ImageSpecField
    from imagekit.processors import ResizeToFill
    from imagekit.utils import get_field_info

    class AvatarThumbnail(ImageSpec):
        format = 'JPEG'
        options = {'quality': 60}

        @property
        def processors(self):
            model, field_name = get_field_info(self.source)
            return [ResizeToFill(model.thumbnail_width, thumbnail.avatar_height)]

    register.generator('myapp:profile:avatar_thumbnail', AvatarThumbnail)

    class Profile(models.Model):
        avatar = models.ImageField(upload_to='avatars')
        avatar_thumbnail = ImageSpecField(source='avatar',
                                          spec_id='myapp:profile:avatar_thumbnail')
        thumbnail_width = models.PositiveIntegerField()
        thumbnail_height = models.PositiveIntegerField()

Now each avatar thumbnail will be resized according to the dimensions stored on
the model!

Of course, processors aren't the only thing that can vary based on the model of
the source image; spec behavior can change in any way you want.


Optimizing
==========

Unlike Django's ImageFields, ImageKit's ImageSpecFields and template tags don't
persist any data in the database. Therefore, in order to know whether an image
file needs to be generated, ImageKit needs to check if the file already exists
(using the appropriate `file storage object`__). The object responsible for
performing these checks is called a *cache file backend*.


__ https://docs.djangoproject.com/en/dev/topics/files/#file-storage


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


Deferring Image Generation
--------------------------

As mentioned above, image generation is normally done synchronously. However,
you can also take advantage of deferred generation. In order to do this, you'll
need to do two things: 1) install `django-celery`__ and 2) tell ImageKit to use
the async cachefile backend. You can do this either on a per-spec basis (by
setting the ``cachefile_backend`` attribute), or for your project by setting
``IMAGEKIT_DEFAULT_CACHEFILE_BACKEND`` in your settings.py:

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
source registered with ImageKit will automatically cause its specs' files to be
generated when it is created or changed.

.. note::

    In order to understand source registration, read :ref:`source-groups`

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


.. _source-groups:

Source Groups
=============

When you run the ``generateimages`` management command, how does ImageKit know
which source images to use with which specs? Obviously, when you define an
ImageSpecField, the source image is being connected to a spec, but what's going
on underneath the hood?

The answer is that, when you define an ImageSpecField, ImageKit automatically
creates and registers an object called a *source group*. Source groups are
responsible for two things:

1. They dispatch signals when a source is created, changed, or deleted, and
2. They expose a generator method that enumerates source files.

When these objects are registered (using ``imagekit.register.source_group()``),
their signals will trigger callbacks on the cache file strategies associated
with image specs that use the source. (So, for example, you can chose to
generate a file every time the source image changes.) In addition, the generator
method is used (indirectly) to create the list of files to generate with the
``generateimages`` management command.

Currently, there is only one source group class bundled with ImageKit—the one
used by ImageSpecFields. This source group
(``imagekit.specs.sourcegroups.ImageFieldSourceGroup``) represents an ImageField
on every instance of a particular model. In terms of the above description, the
instance ``ImageFieldSourceGroup(Profile, 'avatar')`` 1) dispatches a signal
every time the image in Profile's avatar ImageField changes, and 2) exposes a
generator method that iterates over every Profile's "avatar" image.

Chances are, this is the only source group you will ever need to use, however,
ImageKit lets you define and register custom source groups easily. This may be
useful, for example, if you're using the template tags "generateimage" and
"thumbnail" and the optimistic cache file strategy. Again, the purpose is
to tell ImageKit which specs are used with which sources (so the
"generateimages" management command can generate those files) and when the
source image has been created or changed (so that the strategy has the
opportunity to act on it).

A simple example of a custom source group class is as follows:

.. code-block:: python

    import glob
    import os

    class JpegsInADirectory(object):
        def __init__(self, dir):
            self.dir = dir

        def files(self):
            os.chdir(self.dir)
            for name in glob.glob('*.jpg'):
                yield open(name)

Instances of this class could then be registered with one or more spec id:

.. code-block:: python

    from imagekit import register

    register.source_group('myapp:profile:avatar_thumbnail', JpegsInADirectory('/path/to/some/pics'))

Running the "generateimages" management command would now cause thumbnails to be
generated (using the "myapp:profile:avatar_thumbnail" spec) for each of the
JPEGs in `/path/to/some/pics`.

Note that, since this source group doesnt send the `source_created` or
`source_changed` signals, the corresponding cache file strategy callbacks
would not be called for them.
