Upgrading from 2.x
==================

ImageKit 3.0 introduces new APIs and tools that augment, improve, and in some
cases entirely replace old IK workflows. Below, you'll find some useful guides
for migrating your ImageKit 2.0 apps over to the shiny new IK3.


Model Specs
-----------

IK3 is chock full of new features and better tools for even the most
sophisticated use cases. Despite this, not too much has changed when it
comes to the most common of use cases: processing an ``ImageField`` on a model.

In IK2, you may have used an ``ImageSpecField`` on a model to process an
existing ``ImageField``:

.. code-block:: python

    class Profile(models.Model):
        avatar = models.ImageField(upload_to='avatars')
        avatar_thumbnail = ImageSpecField(image_field='avatar',
                                          processors=[ResizeToFill(100, 50)],
                                          format='JPEG',
                                          options={'quality': 60})

In IK3, things look much the same:

.. code-block:: python

    class Profile(models.Model):
        avatar = models.ImageField(upload_to='avatars')
        avatar_thumbnail = ImageSpecField(source='avatar',
                                          processors=[ResizeToFill(100, 50)],
                                          format='JPEG',
                                          options={'quality': 60})

The major difference is that ``ImageSpecField`` no longer takes an
``image_field`` kwarg. Instead, you define a ``source``.


Image Cache Backends
--------------------

In IK2, you could gain some control over how your cached images were generated
by providing an ``image_cache_backend``:

.. code-block:: python

    class Photo(models.Model):
        ...
        thumbnail = ImageSpecField(..., image_cache_backend=MyImageCacheBackend())

This gave you great control over *how* your images are generated and stored,
but it could be difficult to control *when* they were generated and stored.

IK3 retains the image cache backend concept (now called cache file backends),
but separates the 'when' control out to cache file strategies:

.. code-block:: python

    class Photo(models.Model):
        ...
        thumbnail = ImageSpecField(...,
                                   cachefile_backend=MyCacheFileBackend(),
                                   cachefile_strategy=MyCacheFileStrategy())

If you are using the IK2 default image cache backend setting:

.. code-block:: python

    IMAGEKIT_DEFAULT_IMAGE_CACHE_BACKEND = 'path.to.MyImageCacheBackend'

IK3 provides analogous settings for cache file backends and strategies:

.. code-block:: python

    IMAGEKIT_DEFAULT_CACHEFILE_BACKEND = 'path.to.MyCacheFileBackend'
    IMAGEKIT_DEFAULT_CACHEFILE_STRATEGY = 'path.to.MyCacheFileStrategy'

See the documentation on `cache file backends`_ and `cache file strategies`_
for more details.

.. _`cache file backends`:
.. _`cache file strategies`:


Conditional model ``processors``
--------------------------------

In IK2, an ``ImageSpecField`` could take a ``processors`` callable instead of
an iterable, which allowed processing decisions to made based on other
properties of the model. IK3 does away with this feature for consistency's sake
(if one kwarg could be callable, why not all?), but provides a much more robust
solution: the custom ``spec``. See the `advanced usage`_ documentation for more.

.. _`advanced usage`:


Conditonal ``cache_to`` file names
----------------------------------

IK2 provided a means of specifying custom cache file names for your
image specs by passing a ``cache_to`` callable to an ``ImageSpecField``.
IK3 does away with this feature, again, for consistency.

There is a way to achieve custom file names by overriding your spec's
``cachefile_name``, but it is not recommended, as the spec's default
behavior is to hash the combination of ``source``, ``processors``, ``format``,
and other spec options to ensure that changes to the spec always result in
unique file names. See the documentation on `specs`_ for more.

.. _`specs`:


Processors have moved to PILKit
-------------------------------

Processors have moved to a separate project: `PILKit`_. You should not have to
make any changes to an IK2 project to use PILKit--it should be installed with
IK3, and importing from ``imagekit.processors`` will still work.

.. _`PILKit`: https://github.com/matthewwithanm/pilkit
