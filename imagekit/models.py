import os
from datetime import datetime
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.db.models.base import ModelBase
from django.db.models.signals import post_delete
from django.utils.html import conditional_escape as escape
from django.utils.translation import ugettext_lazy as _

from imagekit.specs import ImageSpec, Descriptor
from imagekit.lib import *
from imagekit.options import Options
from imagekit.utils import img_to_fobj

# Modify image file buffer size.
ImageFile.MAXBLOCK = getattr(settings, 'PIL_IMAGEFILE_MAXBLOCK', 256 * 2 ** 10)

# Choice tuples for specifying the crop origin.
# These are provided for convenience.
CROP_HORZ_CHOICES = (
    (0, _('left')),
    (1, _('center')),
    (2, _('right')),
)

CROP_VERT_CHOICES = (
    (0, _('top')),
    (1, _('center')),
    (2, _('bottom')),
)


class ImageModelBase(ModelBase):
    """ ImageModel metaclass

    This metaclass parses IKOptions and loads the specified specification
    module.

    """
    def __init__(self, name, bases, attrs):
        if [b for b in bases if isinstance(b, ImageModelBase)]:
            user_opts = getattr(self, 'IKOptions', None)
            
            specs = []
            for k, v in attrs.items():
                if isinstance(v, ImageSpec):
                    setattr(self, k, Descriptor(v, k))
                    specs.append(v)
            
            user_opts.specs = specs
            opts = Options(user_opts)
            setattr(self, '_ik', opts)
        ModelBase.__init__(self, name, bases, attrs)


class ImageModel(models.Model):
    """ Abstract base class implementing all core ImageKit functionality

    Subclasses of ImageModel are augmented with accessors for each defined
    image specification and can override the inner IKOptions class to customize
    storage locations and other options.

    """
    __metaclass__ = ImageModelBase

    class Meta:
        abstract = True

    def admin_thumbnail_view(self):
        if not self._imgfield:
            return None
        prop = getattr(self, self._ik.admin_thumbnail_spec, None)
        if prop is None:
            return 'An "%s" image spec has not been defined.' % \
              self._ik.admin_thumbnail_spec
        else:
            if hasattr(self, 'get_absolute_url'):
                return u'<a href="%s"><img src="%s"></a>' % \
                    (escape(self.get_absolute_url()), escape(prop.url))
            else:
                return u'<a href="%s"><img src="%s"></a>' % \
                    (escape(self._imgfield.url), escape(prop.url))
    admin_thumbnail_view.short_description = _('Thumbnail')
    admin_thumbnail_view.allow_tags = True

    class IKOptions:
        pass

    @property
    def _imgfield(self):
        return getattr(self, self._ik.image_field)

    def _clear_cache(self):
        for spec in self._ik.specs:
            prop = getattr(self, spec.name())
            prop._delete()

    def _pre_cache(self):
        for spec in self._ik.specs:
            if spec.pre_cache:
                prop = getattr(self, spec.name())
                prop._create()

    def save_image(self, name, image, save=True, replace=True):
        if self._imgfield and replace:
            self._imgfield.delete(save=False)
        if hasattr(image, 'read'):
            data = image.read()
        else:
            data = image
        content = ContentFile(data)
        self._imgfield.save(name, content, save)

    def save(self, clear_cache=True, *args, **kwargs):
        super(ImageModel, self).save(*args, **kwargs)

        is_new_object = self._get_pk_val() is None
        if is_new_object:
            clear_cache = False

        if self._imgfield:
            spec = self._ik.preprocessor_spec
            if spec is not None:
                newfile = self._imgfield.storage.open(str(self._imgfield))
                img = Image.open(newfile)
                img, format = spec.process(img, self)
                if format != 'JPEG':
                    imgfile = img_to_fobj(img, format)
                else:
                    imgfile = img_to_fobj(img, format,
                                          quality=int(spec.quality),
                                          optimize=True)
                content = ContentFile(imgfile.read())
                newfile.close()
                name = str(self._imgfield)
                self._imgfield.storage.delete(name)
                self._imgfield.storage.save(name, content)
        if self._imgfield:
            if clear_cache:
                self._clear_cache()
            self._pre_cache()

    def clear_cache(self, **kwargs):
        assert self._get_pk_val() is not None, "%s object can't be deleted because its %s attribute is set to None." % (self._meta.object_name, self._meta.pk.attname)
        self._clear_cache()


post_delete.connect(ImageModel.clear_cache, sender=ImageModel)


