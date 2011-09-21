import os
from datetime import datetime
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.db.models.base import ModelBase
from django.db.models.signals import post_delete
from django.utils.html import conditional_escape as escape
from django.utils.translation import ugettext_lazy as _

from imagekit.fields import ImageSpec
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
        user_opts = getattr(self, 'IKOptions', None)
        specs = []
        default_image_field = getattr(user_opts, 'default_image_field', None)
        
        for k, v in attrs.items():
            if isinstance(v, ImageSpec):
                specs.append(v)
            elif not default_image_field and isinstance(v, models.ImageField):
                default_image_field = k

        user_opts.specs = specs
        user_opts.default_image_field = default_image_field
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

    class IKOptions:
        pass

    @property
    def _imgfields(self):
        return set([spec._get_imgfield(self) for spec in self._ik.specs])
