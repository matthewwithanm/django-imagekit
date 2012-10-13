from .files import ImageSpecFieldFile


class ImageSpecFileDescriptor(object):
    def __init__(self, field, attname):
        self.attname = attname
        self.field = field

    def __get__(self, instance, owner):
        if instance is None:
            return self.field
        else:
            img_spec_file = ImageSpecFieldFile(instance, self.field,
                    self.attname)
            instance.__dict__[self.attname] = img_spec_file
            return img_spec_file

    def __set__(self, instance, value):
        instance.__dict__[self.attname] = value
