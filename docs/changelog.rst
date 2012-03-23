Changelog
=========

v2.0.0
------

- Added the concept of cache state backends. Cache state backends assume
  control of an image's CRUD actions from `ImageSpec` in versions past. The
  default backend maintins the current behavior: invalidating an image and
  deleting it, then validating that it creates the file if it doesn't already
  exist. One can create custom cache state backends to control how their
  images are cached (e.g., Celery, etc.).

  ImageKit ships with three built-in backends:

  - ``imagecache.base.PessimisticImageCacheBackend`` - A very safe image cache
    backend. Guarantees that files will always be available, but at the cost
    of hitting the storage backend.
  - ``imagecache.base.NonValidatingImageCacheBackend`` - A backend that is
    super optimistic about the existence of spec files. It will hit your file
    storage much less frequently than the pessimistic backend, but it is
    technically possible for a cache file to be missing after validation.
  - ``imagecache.celery.CeleryImageCacheBackend`` - A pessimistic cache state
    backend that uses celery to generate its spec images. Like
    ``PessimisticCacheStateBackend``, this one checks to see if the file
    exists on validation, so the storage is hit fairly frequently, but an
    image is guaranteed to exist. However, while validation guarantees the
    existence of *an* image, it does not necessarily guarantee that you will
    get the correct image, as the spec may be pending regeneration. In other
    words, while there are `generate` tasks in the queue, it is possible to
    get a stale spec image. The tradeoff is that calling `invalidate()`
    won't block to interact with file storage.

- ``resize.Crop`` has been renamed to ``resize.Fill``. Using ``resize.Crop``
  will throw a ``DeprecationWarning``.

- New processors have been added:

  - ``crop.BasicCrop`` - Crop using provided box.
  - ``crop.SmartCrop`` - Crop to provided size, trimming based on entropy.
  - ``crop.TrimBorderColor`` - Trim the specified color from the specified
    sides.
  - ``resize.AddBorder`` - Add a border of specific color and size to an
    image.
  - ``resize.Resize`` - Scale to the provided dimensions (can distort).
  - ``resize.ResizeToCover`` - Scale to the smallest size that will cover
    the specified dimensions. Used internally by ``Fill`` and ``SmartFill``.
  - ``resize.ResizeToFill`` - Scale to fill the provided dimensions,
    trimming away excess using ``Crop``.
  - ``resize.ResizeToFit`` - Scale to fit the provided dimensions.
  - ``resize.ResizeCanvas`` - Takes an image an resizes the canvas, using a
    specific background color if the new size is larger than the current
    image.
  - ``resize.SmartFill`` - Scale to fill the provided dimensions, trimming
    away excess using ``SmartCrop``.

- ``mat_color`` has been added as an arguemnt to the ``ResizeProcessor``. If
  set, the target image size will be enforced and the specified color will be
  used as background color to pad the image.

- We now use `Tox`_ to automate testing.

.. _`Tox`: http://pypi.python.org/pypi/tox


v1.1.0
------

- A ``SmartCrop`` resize processor was added. This allows an image to be
  cropped based on the amount of entropy in the target image's histogram.

- The ``quality`` argument was removed in favor of an ``options`` dictionary.
  This is a more general solution which grants access to PIL's format-specific
  options (including "quality", "progressive", and "optimize" for JPEGs).

- The ``TrimColor`` processor was renamed to ``TrimBorderColor``.

- The private ``_Resize`` class has been removed.


v1.0.3
------

- ``ImageSpec._create()`` was renamed ``ImageSpec.generate()`` and is now
  available in the public API.

- Added an ``AutoConvert`` processor to encapsulate the transparency
  handling logic.

- Refactored transparency handling to be smarter, handling a lot more of
  the situations in which one would convert to or from formats that support
  transparency.

- Fixed PIL zeroing out files when write mode is enabled.


v1.0.2
------

- Added this changelog.

- Enhanced extension detection, format detection, and conversion between the
  two. This eliminates the reliance on an image being loaded into memory
  beforehand in order to detect said image's extension.

- Fixed a regression from the 0.4.x series in which ImageKit was unable to
  convert a PNG file in ``P`` or "palette" mode to JPEG.


v1.0.1
------

- Minor fixes related to the rendering of ``README.rst`` as a reStructured
  text file.

- Fixed the included admin template not being found when ImageKit was  and
  the packaging of the included admin templates.


v1.0
----

- Initial release of the *new* field-based ImageKit API.
