ImageKit is a Django app that helps you to add variations of uploaded images
to your models. These variations are called "specs" and can include things
like different sizes (e.g. thumbnails) and black and white versions.


Installation
------------

1. ``pip install django-imagekit``
    (or clone the source and put the imagekit module on your path)
2. Add ``'imagekit'`` to your ``INSTALLED_APPS`` list in your project's settings.py


Adding Specs to a Model
-----------------------

Much like ``django.db.models.ImageField``, Specs are defined as properties
of a model class::

    from django.db import models
    from imagekit.models import ImageSpec

    class Photo(models.Model):
        original_image = models.ImageField(upload_to='photos')
        formatted_image = ImageSpec(image_field='original_image', format='JPEG',
                quality=90)

Accessing the spec through a model instance will create the image and return
an ImageFile-like object (just like with a normal
``django.db.models.ImageField``)::

    photo = Photo.objects.all()[0]
    photo.original_image.url # > '/media/photos/birthday.tiff'
    photo.formatted_image.url # > '/media/cache/photos/birthday_formatted_image.jpeg'

Check out ``imagekit.models.ImageSpec`` for more information.


Processors
----------

The real power of ImageKit comes from processors. Processors take an image, do
something to it, and return the result. By providing a list of processors to
your spec, you can expose different versions of the original image::

    from django.db import models
    from imagekit.models import ImageSpec
    from imagekit.processors import resize, Adjust

    class Photo(models.Model):
        original_image = models.ImageField(upload_to='photos')
        thumbnail = ImageSpec([Adjust(contrast=1.2, sharpness=1.1),
                resize.Crop(50, 50)], image_field='original_image',
                format='JPEG', quality=90)

The ``thumbnail`` property will now return a cropped image::

    photo = Photo.objects.all()[0]
    photo.thumbnail.url # > '/media/cache/photos/birthday_thumbnail.jpeg'
    photo.thumbnail.width # > 50
    photo.original_image.width # > 1000

The original image is not modified; ``thumbnail`` is a new file that is the
result of running the ``imagekit.processors.resize.Crop`` processor on the
original.

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
        watermarked_image = ImageSpec([Watermark()], image_field='original_image',
                format='JPEG', quality=90)


Admin
-----

ImageKit also contains a class named ``imagekit.admin.AdminThumbnail``
for displaying specs (or even regular ImageFields) in the
`Django admin change list`__. AdminThumbnail is used as a property on
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


__ https://docs.djangoproject.com/en/dev/intro/tutorial02/#customize-the-admin-change-list
__ https://docs.djangoproject.com/en/dev/ref/contrib/admin/#django.contrib.admin.ModelAdmin.list_display
