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
