import os
from StringIO import StringIO

from django.core.files.base import ContentFile

from .processors import ProcessorPipeline, AutoConvert
from .utils import img_to_fobj, open_image, \
        format_to_extension, extension_to_format, UnknownFormatError, \
        UnknownExtensionError


class SpecFileGenerator(object):
    def __init__(self, processors=None, format=None, options={},
            autoconvert=True, storage=None):
        self.processors = processors
        self.format = format
        self.options = options
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
        if not format:
            # Try to guess the format from the extension.
            extension = os.path.splitext(filename)[1].lower()
            if extension:
                try:
                    format = extension_to_format(extension)
                except UnknownExtensionError:
                    pass
        format = format or img.format or original_format or 'JPEG'

        # Run the AutoConvert processor
        if self.autoconvert:
            autoconvert_processor = AutoConvert(format)
            img = autoconvert_processor.process(img)
            options = dict(autoconvert_processor.save_kwargs.items() + \
                    options.items())

        imgfile = img_to_fobj(img, format, **options)
        content = ContentFile(imgfile.read())
        return img, content

    def suggest_extension(self, name):
        original_extension = os.path.splitext(name)[1]
        try:
            suggested_extension = format_to_extension(self.format)
        except UnknownFormatError:
            extension = original_extension
        else:
            if suggested_extension.lower() == original_extension.lower():
                extension = original_extension
            else:
                try:
                    original_format = extension_to_format(original_extension)
                except UnknownExtensionError:
                    extension = suggested_extension
                else:
                    # If the formats match, give precedence to the original extension.
                    if self.format.lower() == original_format.lower():
                        extension = original_extension
                    else:
                        extension = suggested_extension
        return extension

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
