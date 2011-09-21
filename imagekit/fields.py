from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string


class AdminThumbnailView(object):
    short_description = _('Thumbnail')
    allow_tags = True

    def __init__(self, image_field, template=None):
        """
        Keyword arguments:
        image_field -- the name of the ImageField or ImageSpec on the model to
                use for the thumbnail.
        template -- the template with which to render the thumbnail

        """
        self.image_field = image_field
        self.template = template

    def __get__(self, obj, type=None):
        return BoundAdminThumbnailView(obj, self)


class BoundAdminThumbnailView(AdminThumbnailView):
    def __init__(self, model_instance, unbound_field):
        super(BoundAdminThumbnailView, self).__init__(unbound_field.image_field,
                unbound_field.template)
        self.model_instance = model_instance

    def __unicode__(self):
        thumbnail = getattr(self.model_instance, self.image_field, None)
        
        if not thumbnail:
            raise Exception('The property {0} is not defined on {1}.'.format(
                    self.model_instance, self.image_field))

        original_image = getattr(thumbnail, '_imgfield', None) or thumbnail
        template = self.template or 'imagekit/admin/thumbnail.html'

        return render_to_string(template, {
            'model': self.model_instance,
            'thumbnail': thumbnail,
            'original_image': original_image,
        })
    
    def __get__(self, obj, type=None):
        """Override AdminThumbnailView's implementation."""
        return self
