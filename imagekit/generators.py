import os
from StringIO import StringIO

from .processors import ProcessorPipeline
from .utils import (img_to_fobj, open_image, IKContentFile, extension_to_format,
        UnknownExtensionError)


class SpecFileGenerator(object):
    def __init__(self, processors=None, format=None, options=None,
            autoconvert=True, storage=None):
        self.processors = processors
        self.format = format
        self.options = options or {}
        self.autoconvert = autoconvert
        self.storage = storage

    def process_content(self, content, filename=None, source_file=None):
        img = open_image(content)
        original_format = img.format

        # Run the processors
        processors = self.processors
        if callable(processors):
            processors = processors(source_file)
        img = ProcessorPipeline(processors or []).process(img)

        options = dict(self.options or {})

        # Determine the format.
        format = self.format
        if filename and not format:
            # Try to guess the format from the extension.
            extension = os.path.splitext(filename)[1].lower()
            if extension:
                try:
                    format = extension_to_format(extension)
                except UnknownExtensionError:
                    pass
        format = format or img.format or original_format or 'JPEG'

        imgfile = img_to_fobj(img, format, **options)
        content = IKContentFile(filename, imgfile.read(), format=format)
        return img, content

    def generate_file(self, filename, source_file, save=True):
        """
        Generates a new image file by processing the source file and returns
        the content of the result, ready for saving.

        """
        if source_file:  # TODO: Should we error here or something if the source_file doesn't exist?
            # Process the original image file.

            try:
                fp = source_file.storage.open(source_file.name)
            except IOError:
                return
            fp.seek(0)
            fp = StringIO(fp.read())

            img, content = self.process_content(fp, filename, source_file)

            if save:
                storage = self.storage or source_file.storage
                storage.save(filename, content)

            return content
