from .files import ImageSpecFieldFile


class BoundImageKitMeta(object):
    def __init__(self, instance, spec_fields):
        self.instance = instance
        self.spec_fields = spec_fields

    @property
    def spec_files(self):
        return [getattr(self.instance, n) for n in self.spec_fields]


class ImageKitMeta(object):
    def __init__(self, spec_fields=None):
        self.spec_fields = spec_fields or []

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            ik = BoundImageKitMeta(instance, self.spec_fields)
            setattr(instance, '_ik', ik)
            return ik


class ImageSpecFieldDescriptor(object):
    def __init__(self, field, attname):
        self.attname = attname
        self.field = field

    def __get__(self, instance, owner):
        if instance is None:
            return self.field
        else:
            img_spec_file = ImageSpecFieldFile(instance, self.field,
                    self.attname)
            setattr(instance, self.attname, img_spec_file)
            return img_spec_file
