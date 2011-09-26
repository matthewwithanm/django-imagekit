Getting Started
===============

ImageKit is a Django app that helps you to add variations of uploaded images to
your models. These variations are called "specs" and can include things like
different sizes (e.g. thumbnails) and black and white versions.


Adding Specs to a Model
-----------------------

Much like :class:`django.db.models.ImageField`, Specs are defined as properties
of a model class::

    from django.db import models
    from imagekit.models import ImageSpec

    class Photo(models.Model):
        original_image = models.ImageField(upload_to'photos')
        formatted_image = ImageSpec(image_field='original_image', format='JPEG',
                quality=90)

Accessing the spec through a model instance will create the image and return an
ImageFile-like object (just like with a normal
:class:`django.db.models.ImageField`)::

    photo = Photo.objects.all()[0]
    photo.original_image.url # > '/media/photos/birthday.tiff'
    photo.formatted_image.url # > '/media/cache/photos/birthday_formatted_image.jpeg'

Check out :class:`imagekit.models.ImageSpec` for more information.


Processors
----------

The real power of ImageKit comes from processors. Processors take an image, do
something to it, and return the result. By providing a list of processors to
your spec, you can expose different versions of the original image::

    from django.db import models
    from imagekit.models import ImageSpec
    from imagekit.processors import Crop, Adjust

    class Photo(models.Model):
        original_image = models.ImageField(upload_to'photos')
        thumbnail = ImageSpec([Adjust(contrast=1.2, sharpness=1.1), Crop(50, 50)],
                image_field='original_image', format='JPEG', quality=90)

The ``thumbnail`` property will now return a cropped image::

    photo = Photo.objects.all()[0]
    photo.thumbnail.url # > '/media/cache/photos/birthday_thumbnail.jpeg'
    photo.thumbnail.width # > 50
    photo.original_image.width # > 1000

The original image is not modified; ``thumbnail`` is a new file that is the
result of running the :class:`imagekit.processors.Crop` processor on the
original.

The :mod:`imagekit.processors` module contains processors for many common
image manipulations, like resizing, rotating, and color adjustments. However, if
they aren't up to the task, you can create your own. All you have to do is
implement a ``process()`` method::

    class Watermark(object):
        def process(self, image):
            # Code for adding the watermark goes here.
            return image

    class Photo(models.Model):
        original_image = models.ImageField(upload_to'photos')
        watermarked_image = ImageSpec([Watermark()], image_field='original_image',
                format='JPEG', quality=90)


Admin
-----

ImageKit also contains a class named :class:`imagekit.models.AdminThumbnailView`
for displaying specs (or even regular ImageFields) in the
`Django admin change list`__. Like :class:`imagekit.models.ImageSpec`,
AdminThumbnailView is used as a property on Django model classes::

    from django.db import models
    from imagekit.models import ImageSpec
    from imagekit.processors import Crop, AdminThumbnailView

    class Photo(models.Model):
        original_image = models.ImageField(upload_to'photos')
        thumbnail = ImageSpec([Crop(50, 50)], image_field='original_image')
        admin_thumbnail_view = AdminThumbnailView(image_field='thumbnail')

You can then then add this property to the `list_display`__ field of your admin
class::

    from django.contrib import admin
    from .models import Photo


    class PhotoAdmin(admin.ModelAdmin):
        list_display = ('__str__', 'admin_thumbnail_view')


    admin.site.register(Photo, PhotoAdmin)

AdminThumbnailView can even use a custom template. For more information, see
:class:`imagekit.models.AdminThumbnailView`.


Commands
--------

.. automodule:: imagekit.management.commands.ikflush





Digging Deeper
--------------

.. toctree::

    apireference


__ https://docs.djangoproject.com/en/dev/intro/tutorial02/#customize-the-admin-change-list
__ https://docs.djangoproject.com/en/dev/ref/contrib/admin/#django.contrib.admin.ModelAdmin.list_display