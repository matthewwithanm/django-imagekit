from ...files import ImageSpecFile
from django.db.models.fields.files import ImageField


class ImageSpecFileDescriptor(object):
    def __init__(self, field, attname):
        self.attname = attname
        self.field = field

    def __get__(self, instance, owner):
        if instance is None:
            return self.field
        else:
            field_name = getattr(self.field, 'image_field', None)
            if field_name:
                source_file = getattr(instance, field_name)
            else:
                image_fields = [getattr(instance, f.attname) for f in \
                        instance.__class__._meta.fields if \
                        isinstance(f, ImageField)]
                if len(image_fields) == 0:
                    raise Exception('%s does not define any ImageFields, so your' \
                            ' %s ImageSpecField has no image to act on.' % \
                            (instance.__class__.__name__, self.attname))
                elif len(image_fields) > 1:
                    raise Exception('%s defines multiple ImageFields, but you' \
                            ' have not specified an image_field for your %s' \
                            ' ImageSpecField.' % (instance.__class__.__name__,
                            self.attname))
                else:
                    source_file = image_fields[0]
            img_spec_file = ImageSpecFile(self.field.spec, source_file,
                                          self.attname)
            instance.__dict__[self.attname] = img_spec_file
            return img_spec_file

    def __set__(self, instance, value):
        instance.__dict__[self.attname] = value
