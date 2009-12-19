import os
from datetime import datetime
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.db.models.base import ModelBase
from django.utils.html import conditional_escape as escape
from django.utils.translation import ugettext_lazy as _

from imagekit import specs
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
    def __init__(cls, name, bases, attrs):
        parents = [b for b in bases if isinstance(b, ImageModelBase)]
        if not parents:
            return
        user_opts = getattr(cls, 'IKOptions', None)
        opts = Options(user_opts)
        try:
            module = __import__(opts.spec_module,  {}, {}, [''])
        except ImportError:
            raise ImportError('Unable to load imagekit config module: %s' % \
                opts.spec_module)
        for spec in [spec for spec in module.__dict__.values() \
                     if isinstance(spec, type) \
                     and issubclass(spec, specs.ImageSpec) \
                     and spec != specs.ImageSpec]:
            setattr(cls, spec.name(), specs.Descriptor(spec))
            opts.specs.append(spec)
        setattr(cls, '_ik', opts)


class ImageModel(models.Model):
    """ Abstract base class implementing all core ImageKit functionality

    Subclasses of ImageModel are augmented with accessors for each defined
    image specification and can override the inner IKOptions class to customize
    storage locations and other options.

    """
    __metaclass__ = ImageModelBase

    class Meta:
        abstract = True

    class IKOptions:
        pass

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

    @property
    def _imgfield(self):
        return getattr(self, self._ik.image_field)

    @property
    def _storage(self):
        return getattr(self._ik, 'storage', self._imgfield.storage)

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
        is_new_object = self._get_pk_val() is None
        super(ImageModel, self).save(*args, **kwargs)
        if is_new_object:
            clear_cache = False
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
        if clear_cache and self._imgfield != '':
            self._clear_cache()
        self._pre_cache()

    def delete(self):
        assert self._get_pk_val() is not None, "%s object can't be deleted because its %s attribute is set to None." % (self._meta.object_name, self._meta.pk.attname)
        self._clear_cache()
        models.Model.delete(self)
