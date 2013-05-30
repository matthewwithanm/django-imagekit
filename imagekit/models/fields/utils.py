from ...cachefiles import ImageCacheFile


class ImageSpecFileDescriptor(object):
    def __init__(self, field, attname, source_field_name):
        self.attname = attname
        self.field = field
        self.source_field_name = source_field_name

    def __get__(self, instance, owner):
        if instance is None:
            return self.field
        else:
            source = getattr(instance, self.source_field_name)
            spec = self.field.get_spec(source=source)
            file = ImageCacheFile(spec)
            instance.__dict__[self.attname] = file
            return file

    def __set__(self, instance, value):
        instance.__dict__[self.attname] = value
