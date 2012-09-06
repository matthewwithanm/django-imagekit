Changelog
=========

v2.0.1
------

- Fixed a file descriptor leak in the `utils.quiet()` context manager.


v2.0.0
------

- Added the concept of image cache backends. Image cache backends assume
  control of validating and invalidating the cached images from `ImageSpec` in
  versions past. The default backend maintins the current behavior: invalidating
  an image deletes it, while validating checks whether the file exists and
  creates the file if it doesn't. One can create custom image cache backends to
  control how their images are cached (e.g., Celery, etc.).

  ImageKit ships with three built-in backends:

  - ``imagekit.imagecache.PessimisticImageCacheBackend`` - A very safe image
    cache backend. Guarantees that files will always be available, but at the
    cost of hitting the storage backend.
  - ``imagekit.imagecache.NonValidatingImageCacheBackend`` - A backend that is
    super optimistic about the existence of spec files. It will hit your file
    storage much less frequently than the pessimistic backend, but it is
    technically possible for a cache file to be missing after validation.
  - ``imagekit.imagecache.celery.CeleryImageCacheBackend`` - A pessimistic cache
    state backend that uses celery to generate its spec images. Like
    ``PessimisticCacheStateBackend``, this one checks to see if the file
    exists on validation, so the storage is hit fairly frequently, but an
    image is guaranteed to exist. However, while validation guarantees the
    existence of *an* image, it does not necessarily guarantee that you will
    get the correct image, as the spec may be pending regeneration. In other
    words, while there are ``generate`` tasks in the queue, it is possible to
    get a stale spec image. The tradeoff is that calling ``invalidate()``
    won't block to interact with file storage.

- Some of the processors have been renamed and several new ones have been added:

  - ``imagekit.processors.ResizeToFill`` - (previously
    ``imagekit.processors.resize.Crop``) Scales the image to fill the provided
    dimensions and then trims away the excess.
  - ``imagekit.processors.ResizeToFit`` - (previously
    ``imagekit.processors.resize.Fit``) Scale to fit the provided dimensions.
  - ``imagekit.processors.SmartResize`` - Like ``ResizeToFill``, but crops using
    entroy (``SmartCrop``) instead of an anchor argument.
  - ``imagekit.processors.BasicCrop`` - Crop using provided box.
  - ``imagekit.processors.SmartCrop`` - (previously
    ``imagekit.processors.resize.SmartCrop``) Crop to provided size, trimming
    based on entropy.
  - ``imagekit.processors.TrimBorderColor`` - Trim the specified color from the
    specified sides.
  - ``imagekit.processors.AddBorder`` - Add a border of specific color and
    thickness to an image.
  - ``imagekit.processors.Resize`` - Scale to the provided dimensions (can distort).
  - ``imagekit.processors.ResizeToCover`` - Scale to the smallest size that will
    cover the specified dimensions. Used internally by ``Fill`` and
    ``SmartFill``.
  - ``imagekit.processors.ResizeCanvas`` - Takes an image an resizes the canvas,
    using a specific background color if the new size is larger than the current
    image.

- ``mat_color`` has been added as an arguemnt to ``ResizeToFit``. If set, the
  the target image size will be enforced and the specified color will be
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
