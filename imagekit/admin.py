from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string


class AdminThumbnail(object):
    """
    A convenience utility for adding thumbnails to Django's admin change list.

    """
    short_description = _('Thumbnail')
    allow_tags = True

    def __init__(self, image_field, template=None, image_fk=None):
        """
        :param image_field: The name of the ImageField or ImageSpecField on the
            model to use for the thumbnail.
        :param template: The template with which to render the thumbnail
        :param image_fk: The name of the filed that links to the ImageField

        """
        self.image_field = image_field
        self.template = template
        self.image_fk = image_fk

    def __call__(self, obj):
        #Test for image_fk
        if self.image_fk == None:
            thumbnail = getattr(obj, self.image_field, None)
        else:
            thumbnail = getattr(getattr(obj, self.image_fk), self.image_field, None)

        if not thumbnail:
            try:
                thumbnail = getattr(obj, self.image_field)
            except AttributeError:
                raise Exception('The property %s is not defined on %s.' % \
                        (self.image_field, obj.__class__.__name__))

        original_image = getattr(thumbnail, 'source_file', None) or thumbnail
        template = self.template or 'imagekit/admin/thumbnail.html'


        return render_to_string(template, {
            'model': obj,
            'thumbnail': thumbnail,
            'original_image': original_image,
        })

