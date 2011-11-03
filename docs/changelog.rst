Changelog
=========

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
