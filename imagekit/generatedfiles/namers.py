from django.conf import settings
import os
from ..utils import format_to_extension, suggest_extension


def source_name_as_path(generator):
    source_filename = getattr(generator.source, 'name', None)

    if source_filename is None or os.path.isabs(source_filename):
        # Generally, we put the file right in the generated file directory.
        dir = settings.IMAGEKIT_GENERATED_FILE_DIR
    else:
        # For source files with relative names (like Django media files),
        # use the source's name to create the new filename.
        dir = os.path.join(settings.IMAGEKIT_GENERATED_FILE_DIR,
                           os.path.splitext(source_filename)[0])

    ext = suggest_extension(source_filename or '', generator.format)
    return os.path.normpath(os.path.join(dir,
                                         '%s%s' % (generator.get_hash(), ext)))


def source_name_dot_hash(generator):
    source_filename = getattr(generator.source, 'name', None)

    if source_filename is None or os.path.isabs(source_filename):
        # Generally, we put the file right in the generated file directory.
        dir = settings.IMAGEKIT_GENERATED_FILE_DIR
    else:
        # For source files with relative names (like Django media files),
        # use the source's name to create the new filename.
        dir = os.path.join(settings.IMAGEKIT_GENERATED_FILE_DIR,
                           os.path.dirname(source_filename))

    ext = suggest_extension(source_filename or '', generator.format)
    basename = os.path.basename(source_filename)
    return os.path.normpath(os.path.join(dir, '%s.%s%s' % (
            os.path.splitext(basename)[0], generator.get_hash()[:12], ext)))


def hash(generator):
    format = getattr(generator, 'format', None)
    ext = format_to_extension(format) if format else ''
    return os.path.normpath(os.path.join(settings.IMAGEKIT_GENERATED_FILE_DIR,
                                         '%s%s' % (generator.get_hash(), ext)))
