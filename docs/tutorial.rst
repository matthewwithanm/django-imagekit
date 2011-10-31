.. _ref-tutorial:

ImageKit in 7 Steps
===================

Step 1
******

::

    $ pip install django-imagekit

(or clone the source and put the imagekit module on your path)

Step 2
******

Add ImageKit to your models.

::

    # myapp/models.py

    from django.db import models
    from imagekit.models import ImageModel

    class Photo(ImageModel):
        name = models.CharField(max_length=100)
        original_image = models.ImageField(upload_to='photos')
        num_views = models.PositiveIntegerField(editable=False, default=0)

        class IKOptions:
            # This inner class is where we define the ImageKit options for the model
            spec_module = 'myapp.specs'
            cache_dir = 'photos'
            image_field = 'original_image'
            save_count_as = 'num_views'

Step 3
******

Create your specifications.

::

    # myapp/specs.py

    from imagekit.specs import ImageSpec
    from imagekit import processors

    # first we define our thumbnail resize processor
    class ResizeThumb(processors.Resize):
        width = 100
        height = 75
        crop = True

    # now we define a display size resize processor
    class ResizeDisplay(processors.Resize):
        width = 600

    # now let's create an adjustment processor to enhance the image at small sizes
    class EnchanceThumb(processors.Adjustment):
        contrast = 1.2
        sharpness = 1.1

    # now we can define our thumbnail spec
    class Thumbnail(ImageSpec):
        access_as = 'thumbnail_image'
        pre_cache = True
        processors = [ResizeThumb, EnchanceThumb]

    # and our display spec
    class Display(ImageSpec):
        increment_count = True
        processors = [ResizeDisplay]

Step 4
******

Flush the cache and pre-generate thumbnails (ImageKit has to be added to ``INSTALLED_APPS`` for management command to work).

::

    $ python manage.py ikflush myapp

Step 5
******

Use your new model in templates.

::

    <div class="original">
    <img src="{{ photo.original_image.url }}" alt="{{ photo.name }}">
    </div>

    <div class="display">
    <img src="{{ photo.display.url }}" alt="{{ photo.name }}">
    </div>

    <div class="thumbs">
    {% for p in photos %}
    <img src="{{ p.thumbnail_image.url }}" alt="{{ p.name }}">
    {% endfor %}
    </div>

Step 6
******

Play with the API.

::

    >>> from myapp.models import Photo
    >>> p = Photo.objects.all()[0]
    <Photo: MyPhoto>
    >>> p.display.url
    u'/static/photos/myphoto_display.jpg'
    >>> p.display.width
    600
    >>> p.display.height
    420
    >>> p.display.image
    <JpegImagePlugin.JpegImageFile instance at 0xf18990>
    >>> p.display.file
    <File: /path/to/media/photos/myphoto_display.jpg>
    >>> p.display.spec
    <class 'myapp.specs.Display'>

Step 7
******

Enjoy a nice beverage.

::

    from refrigerator import beer

    beer.enjoy()


