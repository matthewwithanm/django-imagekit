Changelog
=========

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
