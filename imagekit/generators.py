from django.conf import settings
from hashlib import md5
import os
import pickle
from .lib import StringIO
from .processors import ProcessorPipeline
from .utils import (img_to_fobj, open_image, IKContentFile, extension_to_format,
        suggest_extension, UnknownExtensionError)


class SpecFileGenerator(object):
    def __init__(self, processors=None, format=None, options=None,
            autoconvert=True, storage=None):
        self.processors = processors
        self.format = format
        self.options = options or {}
        self.autoconvert = autoconvert
        self.storage = storage

    def get_processors(self, source_file):
        processors = self.processors
        if callable(processors):
            processors = processors(source_file)
        return processors

    def process_content(self, content, filename=None, source_file=None):
        img = open_image(content)
        original_format = img.format

        # Run the processors
        processors = self.get_processors(source_file)
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

    def get_hash(self, source_file):
        return md5(''.join([
            source_file.name,
            pickle.dumps(self.get_processors(source_file)),
            self.format,
            pickle.dumps(self.options),
            str(self.autoconvert),
        ])).hexdigest()

    def generate_filename(self, source_file):
        source_filename = source_file.name
        filename = None
        if source_filename:
            hash = self.get_hash(source_file)
            extension = suggest_extension(source_filename, self.format)
            filename = os.path.normpath(os.path.join(
                    settings.IMAGEKIT_CACHE_DIR,
                    os.path.splitext(source_filename)[0],
                    '%s%s' % (hash, extension)))

        return filename

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
