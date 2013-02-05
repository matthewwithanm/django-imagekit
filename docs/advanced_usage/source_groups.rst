.. _source-groups:

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
