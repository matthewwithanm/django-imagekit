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
                                          id='myapp:profile:avatar_thumbnail')

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
                                          id='myapp:profile:avatar_thumbnail')
        thumbnail_width = models.PositiveIntegerField()
        thumbnail_height = models.PositiveIntegerField()

Now each avatar thumbnail will be resized according to the dimensions stored on
the model!

Of course, processors aren't the only thing that can vary based on the model of
the source image; spec behavior can change in any way you want.


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

1. They dispatch signals when a source is saved, and
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

Note that, since this source group doesnt send the `source_saved` signal, the
corresponding cache file strategy callbacks would not be called for them.

