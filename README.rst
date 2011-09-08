===============
django-imagekit
===============

ImageKit In 6 Steps
===================

Step 1
******

::

    $ pip install django-imagekit

(or clone the source and put the imagekit module on your path)

Step 2
******

Create an ImageModel subclass and add specs to it.

::

    # myapp/models.py

    from django.db import models
    from imagekit.models import ImageModel
    from imagekit.specs import ImageSpec
    from imagekit.processors import Crop, Fit, Adjust

    class Photo(ImageModel):
        name = models.CharField(max_length=100)
        original_image = models.ImageField(upload_to='photos')
        num_views = models.PositiveIntegerField(editable=False, default=0)

        thumbnail_image = ImageSpec([Crop(100, 75), Adjust(contrast=1.2, sharpness=1.1)], quality=90, pre_cache=True, image_field='original_image', cache_dir='photos')
        display = ImageSpec([Fit(600)], quality=90, increment_count=True, image_field='original_image', cache_dir='photos', save_count_as='num_views')


Of course, you don't have to define your ImageSpecs inline if you don't want to:

::

    # myapp/specs.py

    from imagekit.specs import ImageSpec
    from imagekit.processors import Crop, Fit, Adjust

    class _BaseSpec(ImageSpec):
        quality = 90        
        image_field = 'original_image'
        cache_dir = 'photos'

    class DisplaySpec(_BaseSpec):
        pre_cache = True
        increment_count = True
        save_count_as = 'num_views'
        processors = [Fit(600)]

    class ThumbnailSpec(_BaseSpec):
        processors = [Crop(100, 75), Adjust(contrast=1.2, sharpness=1.1)]

    # myapp/models.py

    from django.db import models
    from imagekit.models import ImageModel
    from myapp.specs import DisplaySpec, ThumbnailSpec

    class Photo(ImageModel):
        name = models.CharField(max_length=100)
        original_image = models.ImageField(upload_to='photos')
        num_views = models.PositiveIntegerField(editable=False, default=0)

        thumbnail_image = ThumbnailSpec()
        display = DisplaySpec()
            

Step 3
******

Flush the cache and pre-generate thumbnails (ImageKit has to be added to ``INSTALLED_APPS`` for management command to work).

::

    $ python manage.py ikflush myapp

Step 4
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

Step 5
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

Step 6
******

Enjoy a nice beverage.

::

    from refrigerator import beer

    beer.enjoy()


