from django.forms import ImageField
import os
from ..generators import SpecFileGenerator
from ..utils import (extension_to_format, format_to_extension,
        UnknownExtensionError)


class ImageProcessingField(ImageField):

    def __init__(self, processors=None, format=None, options=None,
            autoconvert=True, *args, **kwargs):
        self.processors = processors
        self.format = format
        self.options = dict(options) if options else {}
        self.autoconvert = autoconvert
        super(ImageProcessingField, self).__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        data = super(ImageProcessingField, self).clean(data, initial)

        if data:
            format = self.format
            filename = data.name

            if not format:
                # If no format was specified, try to use the same format as the
                # input file.
                try:
                    format = extension_to_format(os.path.splitext(filename)[1])
                except UnknownExtensionError:
                    pass
            else:
                # If the format was supplied, try to use a filename with the
                # appropriate extension.
                basename, ext = os.path.splitext(filename)
                new_extension = format_to_extension(format)
                filename = '%s%s' % (basename, new_extension or '')

            generator = SpecFileGenerator(self.processors, format,
                    self.options, self.autoconvert)
            img, data = generator.process_content(data, filename)

            # TODO: Generate a new filename based on the result of
            # process_content()? This is only necessary if format is not
            # provided and the uploaded file has no extension.

        return data
