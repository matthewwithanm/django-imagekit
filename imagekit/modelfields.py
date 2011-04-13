from django.db import models
from django.db.models import fields
from django.db.models.fields import files
from django.db.models import signals


class ICCFileDescriptor(files.FileDescriptor):
    pass

class ICCFieldFile(files.FieldFile):
    """
    File-descended object representing a .icc file
    """
    pass

class ICCField(files.FileField):
    """
    Field representing an ICC color profile.
    """
    attr_class = ICCFieldFile
    descriptor_class = ICCFileDescriptor




class ICCImageFileDescriptor(files.ImageFileDescriptor):
    pass

class ICCImageFieldFile(files.ImageFieldFile):
    pass

class ICCImageField(files.ImageField):
    attr_class = ICCImageFieldFile
    descriptor_class = ICCImageFileDescriptor


