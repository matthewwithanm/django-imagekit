import os, urlparse, numpy, uuid
import cStringIO as StringIO
from datetime import datetime
from django.conf import settings
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models.base import ModelBase
from django.db.models import signals
from django.utils.html import conditional_escape as escape
from django.utils.translation import ugettext_lazy as _
from jogging import logging as logg
from colorsys import rgb_to_hls, hls_to_rgb

from imagekit import specs
from imagekit.lib import *
from imagekit.options import Options
from imagekit.utils import img_to_fobj, md5_for_file
from imagekit.modelfields import VALID_CHANNELS
from imagekit.modelfields import HistogramField, ICCDataField, ICCMetaField, ICCField, ICCHashField
from imagekit.ICCProfile import ICCProfile

# Modify image file buffer size.
ImageFile.MAXBLOCK = getattr(settings, 'PIL_IMAGEFILE_MAXBLOCK', 256 * 2 ** 10)

try:
    _storage = getattr(settings, 'IK_STORAGE', None)()
except:
    _storage = FileSystemStorage()
else:
    if not _storage:
        _storage = FileSystemStorage()

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
    """
    ImageModel metaclass
    
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
            raise ImportError('Unable to load imagekit config module: %s' % opts.spec_module)
        for spec in [spec for spec in module.__dict__.values()]:
            if isinstance(spec, type):
                if issubclass(spec, specs.ImageSpec):
                    if spec != specs.ImageSpec:
                        setattr(cls, spec.name(), specs.Descriptor(spec))
                        opts.specs.append(spec)
        
        setattr(cls, '_ik', opts)


class ImageModel(models.Model):
    """
    Abstract base class implementing all core ImageKit functionality
    
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
        return getattr(self._ik, 'storage')
    
    def _clear_cache(self):
        for spec in self._ik.specs:
            prop = getattr(self, spec.name())
            prop._delete()
    
    def _pre_cache(self):
        for spec in self._ik.specs:
            if spec.pre_cache:
                prop = getattr(self, spec.name())
                prop._create()
    
    @property
    def pilimage(self):
        return Image.open(self._storage.open(self._imgfield.name))
    
    def _get_histogram(self):
        out = []
        if self.pilimage:
            #tensor = numpy.array(self.pilimage.convert('L').histogram())
            #histo,buckets = numpy.histogram(tensor, bins=255)
            #return zip(xrange(len(histo)), histo.flatten().astype(int).tolist())
            return zip(xrange(256), self.pilimage.convert('L').histogram())
    histogram = property(_get_histogram)
    
    def _get_rgb_histogram(self):
        return ('r','g','b') # TOOOO DOOOO
    
    def dominantcolor(self):
        return self.pilimage.quantize(1).convert('RGB').getpixel((0, 0))
    
    def meancolor(self):
        return ImageStat.Stat(self.pilimage).mean
    
    def averagecolor(self):
        return self.pilimage.resize((1, 1), Image.ANTIALIAS).getpixel((0, 0))
    
    def mediancolor(self):
        return reduce((lambda x,y: x[0] > y[0] and x or y), self.pilimage.getcolors(self.pilimage.size[0] * self.pilimage.size[1]))
    
    def topcolors(self, numcolors=3):
        if self.pilimage:
            colors = self.pilimage.getcolors(self.pilimage.size[0] * self.pilimage.size[1])
            fmax = lambda x,y: x[0] > y[0] and x or y
            out = []
            out.append(reduce(fmax, colors))
            for i in range(1, numcolors):
                out.append(reduce(fmax, filter(lambda x: x not in out, colors)))
            return out
        return []
    
    def topsat(self, samplesize=10):
        try:
            return "#" + "".join(map(lambda x: "%02X" % int(x*255),
                map(lambda x: hls_to_rgb(x[0], x[1], x[2]), [
                    reduce(lambda x,y: x[2] > y[2] and x or y,
                        map(lambda x: rgb_to_hls(float(x[1][0])/255, float(x[1][1])/255, float(x[1][2])/255), self.topcolors(samplesize)))
                ])[0]
            ))
        except TypeError:
            return ""
    
    def dominanthex(self):
        return "#%02X%02X%02X" % self.dominantcolor()
    
    def meanhex(self):
        m = self.meancolor()
        return "#%02X%02X%02X" % (int(m[0]), int(m[1]), int(m[2]))
    
    def averagehex(self):
        return "#%02X%02X%02X" % self.averagecolor()
    
    def medianhex(self):
        return "#%02X%02X%02X" % self.mediancolor()[1]
    
    def tophex(self, numcolors=3):
        return [("#%02X%02X%02X" % tc[1]) for tc in self.topcolors(numcolors)]
    
    def save_image(self, name, image, save=True, replace=True):
        logg.info("***")
        logg.info("ABOUT TO SAVE IMAGE WITH save_image() -- ")
        if hasattr(image, 'read'):
            data = image.read()
        else:
            data = image
        
        if self._imgfield and replace:
            self._imgfield.delete(save=False)
        
        content = ContentFile(data)
        self._imgfield.save(name, content, save)
    
    def save(self, clear_cache=False, *args, **kwargs):
        is_new_object = self._get_pk_val() is None
        super(ImageModel, self).save(*args, **kwargs)
        
        if is_new_object and self._imgfield:
            clear_cache = False
        
        if clear_cache:
            self._clear_cache()
        
        self._pre_cache()
    
    def clear_cache(self, **kwargs):
        assert self._get_pk_val() is not None, "%s object can't be deleted because its %s attribute is set to None." % (self._meta.object_name, self._meta.pk.attname)
        self._clear_cache()

signals.post_delete.connect(ImageModel.clear_cache, sender=ImageModel)

HISTOGRAMS = ('luma','rgb')

class HistogramBase(models.Model):
    class Meta:
        abstract = True
        verbose_name = "Histogram"
        verbose_name_plural = "Histograms"
    
    def __init__(self, *args, **kwargs):
        super(HistogramBase, self).__init__(*args, **kwargs)
    
    def __repr__(self):
        return "<%s #%s>" % (self.__class__.__name__, self.pk)
    
    def __getitem__(self, channel):
        if not channel:
            raise KeyError("No channel index specified.")
        if not isinstance(channel, basestring):
            raise TypeError("Channel index must be one of: %s" % ', '.join(VALID_CHANNELS))
        if channel not in VALID_CHANNELS:
            raise IndexError("Channel index must be one of: %s" % ', '.join(VALID_CHANNELS))
        if not hasattr(self, 'image'):
            raise NotImplementedError("No 'image' property found on %s." % repr(self))
        if not self.image:
            raise ValueError("HistogramBase %s has no valid ImageWithMetadata associated with it." % repr(self))
        
        pilimage = self.image.pilimage
        
        if not pilimage:
            raise ValueError("No PIL image defined!")
        
        if channel not in self.keys():
            raise KeyError("%s has no histogram for channel %s." % (repr(self), channel))
        
        return getattr(self, channel)
    
    @property
    def image(self):
        if not hasattr(self, "_parentclass"):
            return None
        if not hasattr(self,  "_%s_image" % self._parentclass.lower()):
            return None
        return getattr(self, "_%s_image" % self._parentclass.lower()).get()
    
    def keys(self):
        out = []
        for field in self._meta.fields:
            if isinstance(field, HistogramField):
                out.append(field.name)
        return out
    
    def values(self):
        out = []
        for field in self._meta.fields:
            if isinstance(field, HistogramField):
                out.append(field.value_from_object(self))
        return out
    
    def items(self):
        return zip(self.keys(), self.values())

class LumaHistogram(HistogramBase):
    class Meta:
        abstract = False
        verbose_name = "Luma Histogram"
        verbose_name_plural = "Luma Histograms"
    
    L = HistogramField(channel='L', verbose_name="Luma")

class RGBHistogram(HistogramBase):
    class Meta:
        abstract = False
        verbose_name = "RGB Histogram"
        verbose_name_plural = "RGB Histograms"
    
    R = HistogramField(channel='R', verbose_name="Red")
    G = HistogramField(channel='G', verbose_name="Green")
    B = HistogramField(channel='B', verbose_name="Blue")

class ImageWithMetadata(ImageModel):
    class Meta:
        abstract = True
        verbose_name = "Image Metadata"
        verbose_name = "Image Metadata Objects"
    
    def __init__(self, *args, **kwargs):
        super(ImageWithMetadata, self).__init__(*args, **kwargs)
        for histogram_type in HISTOGRAMS:
            if hasattr(self, "histogram_%s" % histogram_type):
                related_histogram = getattr(self, "histogram_%s" % histogram_type, None)
                if related_histogram:
                    getattr(self, "histogram_%s" % histogram_type)._parentclass = self.__class__.__name__
    
    histogram_luma = models.ForeignKey(LumaHistogram,
        related_name="_%(class)s_image",
        unique=True,
        blank=True,
        null=True,
        editable=True)
    histogram_rgb = models.ForeignKey(RGBHistogram,
        related_name="_%(class)s_image",
        unique=True,
        blank=True,
        null=True,
        editable=True)
    
    icc = ICCMetaField(verbose_name="ICC data",
        editable=False,
        pil_reference=lambda: 'pilimage',
        null=True)
    
    def save(self, force_insert=False, force_update=False):
        self.save_related_histograms(instance=self)
        super(ImageWithMetadata, self).save(force_insert, force_update)
    
    def save_related_histograms(self, **kwargs): # signal, sender, instance
        """
        Saves a histogram when its related ImageWithMetadata object is about to be saved.
        This should be reimplemented once I figure out how to iterate through an object's FKs
        in a non-retarded way.
        """
        
        metadata = kwargs.get('instance')
        
        for histogram_type in HISTOGRAMS:
            if hasattr(self, "histogram_%s" % histogram_type):
                related_histogram = getattr(self, "histogram_%s" % histogram_type, None)
                if related_histogram:
                    related_histogram.save()

    
    def __repr__(self):
        return "<%s #%s>" % (self.__class__.__name__, self.pk)


class ICCModel(models.Model):
    class Meta:
        abstract = False
        verbose_name = "ICC Profile"
        verbose_name_plural = "ICC Profile Objects"
    
    def __init__(self, *args, **kwargs):
        super(ICCModel, self).__init__(*args, **kwargs)
        self._storage = _storage
    
    iccfile = ICCField(verbose_name="ICC binary file",
        storage=_storage,
        blank=True,
        null=True,
        upload_to="icc/uploads",
        data_field='icc', # points to ICCDataField
        hash_field='icchash', # points to ICCHashField
        max_length=255)
    icc = ICCDataField(verbose_name="ICC data",
        editable=False,
        blank=True,
        null=True)
    icchash = ICCHashField(verbose_name="ICC file hash")
    createdate = models.DateTimeField('Created on',
        default=datetime.now,
        blank=True,
        editable=False)
    modifydate = models.DateTimeField('Last modified on',
        default=datetime.now,
        blank=True,
        editable=False)
    
    def save(self, force_insert=False, force_update=False):
        self.modifydate = datetime.now()
        super(ICCModel, self).save(force_insert, force_update)
    
    def __unicode__(self):
        
        if self.icc:
            return u'%s' % (
                self.icc.getDescription(),
            )
        
        return u'-empty-'
    

