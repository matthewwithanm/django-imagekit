
ImageKit is a Django app that helps you to add variations of uploaded images
to your models. These variations are called "specs" and can include things
like different sizes (e.g. thumbnails) and black and white versions.

**For the complete documentation on the latest stable version of ImageKit, see**
`ImageKit on RTD`_. Our `changelog is also available`_.

.. _`ImageKit on RTD`: http://django-imagekit.readthedocs.org
.. _`changelog is also available`: http://django-imagekit.readthedocs.org/en/latest/changelog.html


Installation
------------

1. Install `PIL`_ or `Pillow`_. If you're using an ``ImageField`` in Django,
   you should have already done this.
2. ``pip install django-imagekit``
   (or clone the source and put the imagekit module on your path)
3. Add ``'imagekit'`` to your ``INSTALLED_APPS`` list in your project's settings.py

.. note:: If you've never seen Pillow before, it considers itself a
   more-frequently updated "friendly" fork of PIL that's compatible with
   setuptools. As such, it shares the same namespace as PIL does and is a
   drop-in replacement.

.. _`PIL`: http://pypi.python.org/pypi/PIL
.. _`Pillow`: http://pypi.python.org/pypi/Pillow


Adding Specs to a Model
-----------------------

Much like ``django.db.models.ImageField``, Specs are defined as properties
of a model class::

    from django.db import models
    from imagekit.models import ImageSpecField

    class Photo(models.Model):
        original_image = models.ImageField(upload_to='photos')
        formatted_image = ImageSpecField(image_field='original_image', format='JPEG',
                options={'quality': 90})

Accessing the spec through a model instance will create the image and return
an ImageFile-like object (just like with a normal
``django.db.models.ImageField``)::

    photo = Photo.objects.all()[0]
    photo.original_image.url # > '/media/photos/birthday.tiff'
    photo.formatted_image.url # > '/media/cache/photos/birthday_formatted_image.jpeg'

Check out ``imagekit.models.ImageSpecField`` for more information.

If you only want to save the processed image (without maintaining the original),
you can use a ``ProcessedImageField``::

    from django.db import models
    from imagekit.models.fields import ProcessedImageField

    class Photo(models.Model):
        processed_image = ImageSpecField(format='JPEG', options={'quality': 90})

See the class documentation for details.


Processors
----------

The real power of ImageKit comes from processors. Processors take an image, do
something to it, and return the result. By providing a list of processors to
your spec, you can expose different versions of the original image::

    from django.db import models
    from imagekit.models import ImageSpecField
    from imagekit.processors import ResizeToFill, Adjust

    class Photo(models.Model):
        original_image = models.ImageField(upload_to='photos')
        thumbnail = ImageSpecField([Adjust(contrast=1.2, sharpness=1.1),
                ResizeToFill(50, 50)], image_field='original_image',
                format='JPEG', options={'quality': 90})

The ``thumbnail`` property will now return a cropped image::

    photo = Photo.objects.all()[0]
    photo.thumbnail.url # > '/media/cache/photos/birthday_thumbnail.jpeg'
    photo.thumbnail.width # > 50
    photo.original_image.width # > 1000

The original image is not modified; ``thumbnail`` is a new file that is the
result of running the ``imagekit.processors.ResizeToFill`` processor on the
original. (If you only need to save the processed image, and not the original,
pass processors to a ``ProcessedImageField`` instead of an ``ImageSpecField``.)

The ``imagekit.processors`` module contains processors for many common
image manipulations, like resizing, rotating, and color adjustments. However,
if they aren't up to the task, you can create your own. All you have to do is
implement a ``process()`` method::

    class Watermark(object):
        def process(self, image):
            # Code for adding the watermark goes here.
            return image

    class Photo(models.Model):
        original_image = models.ImageField(upload_to='photos')
        watermarked_image = ImageSpecField([Watermark()], image_field='original_image',
                format='JPEG', options={'quality': 90})


Admin
-----

ImageKit also contains a class named ``imagekit.admin.AdminThumbnail``
for displaying specs (or even regular ImageFields) in the
`Django admin change list`_. AdminThumbnail is used as a property on
Django admin classes::

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


Image Cache Backends
--------------------

Whenever you access properties like ``url``, ``width`` and ``height`` of an
``ImageSpecField``, its cached image is validated; whenever you save a new image
to the ``ImageField`` your spec uses as a source, the spec image is invalidated.
The default way to validate a cache image is to check to see if the file exists
and, if not, generate a new one; the default way to invalidate the cache is to
delete the image. This is a very simple and straightforward way to handle cache
validation, but it has its drawbacks—for example, checking to see if the image
exists means frequently hitting the storage backend.

Because of this, ImageKit allows you to define custom image cache backends. To
be a valid image cache backend, a class must implement three methods:
``validate``, ``invalidate``, and ``clear`` (which is called when the image is
no longer needed in any form, i.e. the model is deleted). Each of these methods
must accept a file object, but the internals are up to you. For example, you
could store the state (valid, invalid) of the cache in a database to avoid
filesystem access. You can then specify your image cache backend on a per-field
basis::

    class Photo(models.Model):
        ...
        thumbnail = ImageSpecField(..., image_cache_backend=MyImageCacheBackend())

Or in your ``settings.py`` file if you want to use it as the default::

    IMAGEKIT_DEFAULT_IMAGE_CACHE_BACKEND = 'path.to.MyImageCacheBackend'


Contributing
------------

We love contributions! And you don't have to be an expert with the library—or
even Django—to contribute either: ImageKit's processors are standalone classes
that are completely separate from the more intimidating internals of Django's
ORM. If you've written a processor that you think might be useful to other
people, open a pull request so we can take a look!

ImageKit's image cache backends are also fairly isolated from the ImageKit guts.
If you've fine-tuned one to work perfectly for a popular file storage backend,
let us take a look! Maybe other people could use it.
