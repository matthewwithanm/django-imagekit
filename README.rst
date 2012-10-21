ImageKit is a Django app for processing images. Need a thumbnail? A
black-and-white version of a user-uploaded image? ImageKit will make them for
you. If you need to programatically generate one image from another, you need
ImageKit.

**For the complete documentation on the latest stable version of ImageKit, see**
`ImageKit on RTD`_. Our `changelog is also available`_.

.. _`ImageKit on RTD`: http://django-imagekit.readthedocs.org
.. _`changelog is also available`: http://django-imagekit.readthedocs.org/en/latest/changelog.html


Installation
============

1. Install `PIL`_ or `Pillow`_. (If you're using an ``ImageField`` in Django,
   you should have already done this.)
2. ``pip install django-imagekit``
   (or clone the source and put the imagekit module on your path)
3. Add ``'imagekit'`` to your ``INSTALLED_APPS`` list in your project's settings.py

.. note:: If you've never seen Pillow before, it considers itself a
   more-frequently updated "friendly" fork of PIL that's compatible with
   setuptools. As such, it shares the same namespace as PIL does and is a
   drop-in replacement.

.. _`PIL`: http://pypi.python.org/pypi/PIL
.. _`Pillow`: http://pypi.python.org/pypi/Pillow


Usage Overview
==============


Specs
-----

You have one image and you want to do something to it to create another image.
That's the basic use case of ImageKit. But how do you tell ImageKit what to do?
By defining an "image spec." Specs are instructions for creating a new image
from an existing one, and there are a few ways to define one. The most basic
way is by defining an ``ImageSpec`` subclass:

.. code-block:: python

    from imagekit import ImageSpec
    from imagekit.processors import ResizeToFill

    class Thumbnail(ImageSpec):
        processors = [ResizeToFill(100, 50)]
        format = 'JPEG'
        options = {'quality': 60}

Now that you've defined a spec, it's time to use it. The nice thing about specs
is that they can be used in many different contexts.

Sometimes, you may want to just use a spec to generate a new image file. This
might be useful, for example, in view code, or in scripts:

.. code-block:: python

    spec = Thumbnail()
    new_file = spec.apply(source_file)

More often, however, you'll want to register your spec with ImageKit:

.. code-block:: python

    from imagekit import specs
    specs.register('myapp:fancy_thumbnail', Thumbnail)

Once a spec is registered with a unique name, you can start to take advantage of
ImageKit's powerful utilities to automatically generate images for you...

.. note:: You might be wondering why we bother with the id string instead of
   just passing the spec itself. The reason is that these ids allow users to
   easily override specs defined in third party apps. That way, it doesn't
   matter if "django-badblog" says its thumbnails are 200x200, you can just
   register your own spec (using the same id the app uses) and have whatever
   size thumbnails you want.


In Templates
^^^^^^^^^^^^

One utility ImageKit provides for processing images is a template tag:

.. code-block:: html

    {% load imagekit %}

    {% spec 'myapp:fancy_thumbnail' source_image alt='A picture of me' %}

Output:

.. code-block:: html

    <img src="/media/CACHE/ik/982d5af84cddddfd0fbf70892b4431e4.jpg" width="100" height="50" alt="A picture of me" />

Not generating HTML image tags? No problem. The tag also functions as an
assignment tag, providing access to the underlying file object:

.. code-block:: html

    {% load imagekit %}

    {% spec 'myapp:fancy_thumbnail' source_image as th %}
    <a href="{{ th.url }}">Click to download a cool {{ th.width }} x {{ th.height }} image!</a>


In Models
^^^^^^^^^

Specs can also be used to add ``ImageField``-like fields that expose the result
of applying a spec to another one of your model's fields:

.. code-block:: python

    from django.db import models
    from imagekit.models import ImageSpecField

    class Photo(models.Model):
        avatar = models.ImageField(upload_to='avatars')
        avatar_thumbnail = ImageSpecField(id='myapp:fancy_thumbnail', image_field='avatar')

    photo = Photo.objects.all()[0]
    print photo.avatar_thumbnail.url    # > /media/CACHE/ik/982d5af84cddddfd0fbf70892b4431e4.jpg
    print photo.avatar_thumbnail.width  # > 100

Since defining a spec, registering it, and using it in a single model field is
such a common usage, ImakeKit provides a shortcut that allow you to skip
writing a subclass of ``ImageSpec``:

.. code-block:: python

    from django.db import models
    from imagekit.models import ImageSpecField
    from imagekit.processors import ResizeToFill

    class Photo(models.Model):
        avatar = models.ImageField(upload_to='avatars')
        avatar_thumbnail = ImageSpecField(processors=[ResizeToFill(100, 50)],
                                          format='JPEG',
                                          options={'quality': 60},
                                          image_field='avatar')

    photo = Photo.objects.all()[0]
    print photo.avatar_thumbnail.url    # > /media/CACHE/ik/982d5af84cddddfd0fbf70892b4431e4.jpg
    print photo.avatar_thumbnail.width  # > 100

This has the exact same behavior as before, but the spec definition is inlined.
Since no ``id`` is provided, one is automatically generated based on the app
name, model, and field.

Specs can also be used in models to add ``ImageField``-like fields that process
a user-provided image without saving the original:

.. code-block:: python

    from django.db import models
    from imagekit.models import ProcessedImageField

    class Photo(models.Model):
        avatar_thumbnail = ProcessedImageField(spec_id='myapp:fancy_thumbnail',
                                               upload_to='avatars')

    photo = Photo.objects.all()[0]
    print photo.avatar_thumbnail.url    # > /media/avatars/MY-avatar_3.jpg
    print photo.avatar_thumbnail.width  # > 100

Like with ``ImageSpecField``, the ``ProcessedImageField`` constructor also
has a shortcut version that allows you to inline spec definitions.


In Forms
^^^^^^^^

In addition to the model field above, there's also a form field version of the
``ProcessedImageField`` class. The functionality is basically the same (it
processes an image once and saves the result), but it's used in a form class:

.. code-block:: python

    from django import forms
    from imagekit.forms import ProcessedImageField

    class AvatarForm(forms.Form):
        avatar_thumbnail = ProcessedImageField(spec_id='myapp:fancy_thumbnail')

The benefit of using ``imagekit.forms.ProcessedImageField`` (as opposed to
``imagekit.models.ProcessedImageField`` above) is that it keeps the logic for
creating the image outside of your model (in which you would use a normal
Django ``ImageField``). You can even create multiple forms, each with their own
``ProcessedImageField``, that all store their results in the same image field.

As with the model field classes, ``imagekit.forms.ProcessedImageField`` also
has a shortcut version that allows you to inline spec definitions.


Processors
----------

So far, we've only seen one processor: ``imagekit.processors.ResizeToFill``. But
ImageKit is capable of far more than just resizing images, and that power comes
from its processors.

Processors take a PIL image object, do something to it, and return a new one.
A spec can make use of as many processors as you'd like, which will all be run
in order.

.. code-block:: python

    from imagekit import ImageSpec
    from imagekit.processors import TrimBorderColor, Adjust

    class MySpec(ImageSpec):
        processors = [
            TrimBorderColor(),
            Adjust(contrast=1.2, sharpness=1.1),
        ]
        format = 'JPEG'
        options = {'quality': 60}

The ``imagekit.processors`` module contains processors for many common
image manipulations, like resizing, rotating, and color adjustments. However,
if they aren't up to the task, you can create your own. All you have to do is
define a class that implements a ``process()`` method:

.. code-block:: python

    class Watermark(object):
        def process(self, image):
            # Code for adding the watermark goes here.
            return image

That's all there is to it! To use your fancy new custom processor, just include
it in your spec's ``processors`` list:

.. code-block:: python

    from imagekit import ImageSpec
    from imagekit.processors import TrimBorderColor, Adjust
    from myapp.processors import Watermark

    class MySpec(ImageSpec):
        processors = [
            TrimBorderColor(),
            Adjust(contrast=1.2, sharpness=1.1),
            Watermark(),
        ]
        format = 'JPEG'
        options = {'quality': 60}


Admin
-----

ImageKit also contains a class named ``imagekit.admin.AdminThumbnail``
for displaying specs (or even regular ImageFields) in the
`Django admin change list`_. AdminThumbnail is used as a property on
Django admin classes:

.. code-block:: python

    from django.contrib import admin
    from imagekit.admin import AdminThumbnail
    from .models import Photo

    class PhotoAdmin(admin.ModelAdmin):
        list_display = ('__str__', 'admin_thumbnail')
        admin_thumbnail = AdminThumbnail(image_field='thumbnail')

    admin.site.register(Photo, PhotoAdmin)

AdminThumbnail can even use a custom template. For more information, see
``imagekit.admin.AdminThumbnail``.

.. _`Django admin change list`: https://docs.djangoproject.com/en/dev/intro/tutorial02/#customize-the-admin-change-list


Community
---------

Please use `the GitHub issue tracker <https://github.com/jdriscoll/django-imagekit/issues>`_
to report bugs with django-imagekit. `A mailing list <https://groups.google.com/forum/#!forum/django-imagekit>`_
also exists to discuss the project and ask questions, as well as the official
`#imagekit <irc://irc.freenode.net/imagekit>`_ channel on Freenode.


Contributing
------------

We love contributions! And you don't have to be an expert with the library—or
even Django—to contribute either: ImageKit's processors are standalone classes
that are completely separate from the more intimidating internals of Django's
ORM. If you've written a processor that you think might be useful to other
people, open a pull request so we can take a look!
