import os, urlparse, numpy, uuid, random, hashlib
import cStringIO as StringIO
from datetime import datetime
from django.conf import settings
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.core.exceptions import MultipleObjectsReturned
from django.db import models
from django.db.models import Q
from django.db.models import signals
from django.db.models.base import ModelBase
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.utils.html import conditional_escape as escape
from django.utils.translation import ugettext_lazy as _
from jogging import logging as logg
from colorsys import rgb_to_hls, hls_to_rgb

from imagekit import specs
from imagekit.lib import *
from imagekit.options import Options
from imagekit.memoize import memoize
from imagekit.modelfields import to_matrix
from imagekit.modelfields import VALID_CHANNELS
from imagekit.ICCProfile import ICCProfile
from imagekit.utils import img_to_fobj, ADict
from imagekit.delegate import DelegateManager, delegate
from imagekit.modelfields import ICCField, ICCHashField
from imagekit.modelfields import ICCDataField, ICCMetaField
from imagekit.modelfields import HistogramChannelField, Histogram

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
        for spec in module.__dict__.values():
            if isinstance(spec, type):
                if issubclass(spec, specs.ImageSpec):
                    setattr(cls, spec.name(), specs.FileDescriptor(spec))
                    opts.specs.append(spec)
                elif issubclass(spec, specs.MatrixSpec):
                    setattr(cls, spec.name(), specs.MatrixDescriptor(spec))
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

class HistogramBase(models.Model):
    """
    Model representing a 1-dimensional image histogram.
    
    HistogramBase implements a GenericForeignKey to connect to its parent
    ImageWithMetadata instance. The assumption is that ImageWithMetadata
    subclasses use the default PositiveIntegers for their respective
    id fields -- I'm not a super-huge fan of the willy-nilly use of generic
    relations but this is a pretty certifiable use-case; performance is more of an
    issue with the histogram data itself (w/r/t joins and such)
    so I'm OK with it here. Caveat Implementor.
    
    """
    
    class Meta:
        abstract = True
        verbose_name = "Histogram"
        verbose_name_plural = "Histograms"
    
    content_type = models.ForeignKey(ContentType,
        blank=True,
        null=True) # GFK default
    object_id = models.PositiveIntegerField(verbose_name="Object ID",
        blank=True,
        null=True) # GFK default
    imagewithmetadata = generic.GenericForeignKey(
        'content_type',
        'object_id')
    
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
        return self.imagewithmetadata
    
    def keys(self):
        out = []
        for field in self._meta.fields:
            if isinstance(field, HistogramChannelField):
                out.append(field.name)
        return out
    
    def values(self):
        out = []
        for field in self._meta.fields:
            if isinstance(field, HistogramChannelField):
                out.append(self[field.name])
        return out
    
    def items(self):
        return zip(self.keys(), self.values())
    
    # distance:
    # math.sqrt(reduce(operator.add, map(lambda h,i: h*(i**2), abs(axim.histogram_rgb.all - pxim.histogram_rgb.all), range(256*3))) / float(axim.w) * axim.h)
    
    @property
    def all(self):
        out = []
        for channel in self.keys():
            for i in xrange(256):
                out.append(getattr(self, "__%s_%02X" % (channel, i)))
        return to_matrix(out)


"""
HISTOGRAM IMPLEMENTATIONS.

Histograms are subclasses of the abstract base model HistogramBase that are defined with one or more
channels, represented with HistogramChannelFields. Histograms are computed from the PIL representation
of the model object's image data -- the channel flag for each HistogramChannelField in the histogram
has to be a character found in the 'mode' attribute of the PIL image object (pilimage.mode). If you
want to compute a histogram from a dimension that isn't necessarily found in your images' mode attribute,
you can use the pil_reference kwarg as below in LumaHistogram's implementation.

When passed to a HistogramChannelField, the pil_reference kwarg needs to provide either a string
or a callable that will yield a PIL object from which we should extract histogram data. the default
is 'pilimage', which can be expressed with a callable like so:

    class MyHistogram(HistogramBase):
        L = HistogramChannelField(channel="L", pil_reference=lambda instance: getattr(instance, 'pilimage'))

For LumaHistogram, I'm getting the image luminosity data like so:

    class MyHistogram(HistogramBase):
        L = HistogramChannelField(channel="L", pil_reference=lambda instance: instance.pilimage.convert('L'))

More complex callables can be used as well:

    def histogram_with_multmask(instance):
        from PIL import Image, ImageChops
        mask_image = "/home/me/MyShit/maskimage.jpg"
        return ImageChops.multiply(Image.open(mask_image), instance).convert('L')
    
    class MyHistogram(HistogramBase):
        M = HistogramChannelField(channel="L", pil_reference=histogram_with_multmask)

"""


class LumaHistogram(HistogramBase):
    """
    Luma histogram implementation. It uses one 8-bit channel, L -- a copy of
    the related image is converted to 'L' mode, as per "pil_reference" (below)
    and used when populating LumaHistogram during save and instantiation.
    
    """
    class Meta:
        abstract = False
        verbose_name = "Luma Histogram"
        verbose_name_plural = "Luma Histograms"
    
    L = HistogramChannelField(channel='L', verbose_name="Luma", pil_reference=lambda instance: instance.pilimage.convert('L'))

class RGBHistogram(HistogramBase):
    """
    RGB histogram implementation. One channel for each of the primaries in RGB.
    
    """
    class Meta:
        abstract = False
        verbose_name = "RGB Histogram"
        verbose_name_plural = "RGB Histograms"
    
    R = HistogramChannelField(channel='R', verbose_name="Red")
    G = HistogramChannelField(channel='G', verbose_name="Green")
    B = HistogramChannelField(channel='B', verbose_name="Blue")


"""
ImageWithMetadata model.


"""
class ImageWithMetadataQuerySet(models.query.QuerySet):
    
    def __init__(self, *args, **kwargs):
        super(ImageWithMetadataQuerySet, self).__init__(*args, **kwargs)
        random.seed()
    
    @delegate
    def rnd(self):
        return random.choice(self.all())
    
    @delegate
    def with_profile(self, icc=None):
        return self.filter(icc__isnull=False)
    
    @delegate
    def with_matching_profile(self, icc=None, hsh=None):
        if icc:
            if hasattr(icc, 'data'):
                hsh = hashlib.sha1(icc.data).hexdigest()
        if hsh:
            return self.filter(
                icc__isnull=False,
                icchash__exact=hsh,
            )
        return self.none()
    
    @delegate
    def with_different_profile(self, icc=None, hsh=None):
        if icc:
            if hasattr(icc, 'data'):
                hsh = hashlib.sha1(icc.data).hexdigest()
        if hsh:
            return self.filter(
                Q(icc__isnull=False) & \
                ~Q(icchash__exact=hsh)
            )
        return self.none()
    
    @delegate
    def rndicc(self):
        return self.with_profile().rnd()

class ImageWithMetadataManager(DelegateManager):
    __queryset__ = ImageWithMetadataQuerySet

class ImageWithMetadata(ImageModel):
    class Meta:
        abstract = True
        verbose_name = "Image Metadata"
        verbose_name = "Image Metadata Objects"
    
    objects = ImageWithMetadataManager()
    
    # All we got right now is Luma and RGB. Come back tomorrow you want more colorspaces.
    histogram_luma = Histogram(colorspace="Luma")
    histogram_rgb = Histogram(colorspace="RGB")
    icc = ICCMetaField(verbose_name="ICC data",
        hash_field='icchash',
        editable=False,
        null=True)
    icchash = ICCHashField(verbose_name="ICC embedded profile hash",
        unique=False, # ICCHashField defaults to unique=True
        editable=True,
        null=True)
    
    @property
    def iccmodel(self):
        try:
            return ICCModel.objects.get(icchash=self.icchash)
        except ICCModel.DoesNotExist:
            return None
    
    @property
    def same_profile_set(self):
        return self.__class__.objects.with_matching_profile(hsh=self.icchash)
    
    @property
    def different_profile_set(self):
        return self.__class__.objects.with_different_profile(hsh=self.icchash)
    
    @property
    def icctransformer(self):
        return self.icc.transformer
    
    
    def save(self, force_insert=False, force_update=False):
        super(ImageWithMetadata, self).save(force_insert, force_update)
    
    def __repr__(self):
        return "<%s #%s>" % (self.__class__.__name__, self.pk)


class ICCQuerySet(models.query.QuerySet):
    
    def __init__(self, *args, **kwargs):
        super(ICCQuerySet, self).__init__(*args, **kwargs)
        random.seed()
    
    @delegate
    def get_profile_match(self, icc=None):
        if icc:
            if hasattr(icc, 'data'):
                return self.get(
                    icc__isnull=False,
                    icchash__exact=hashlib.sha1(icc.data).hexdigest(),
                )
        return self.none()
    
    @delegate
    def rnd(self):
        return random.choice(self.all())

class ICCManager(DelegateManager):
    __queryset__ = ICCQuerySet

class ICCModel(models.Model):
    class Meta:
        abstract = False
        verbose_name = "ICC Profile"
        verbose_name_plural = "ICC Profile Objects"
    
    def __init__(self, *args, **kwargs):
        super(ICCModel, self).__init__(*args, **kwargs)
        self._storage = _storage
    
    objects = ICCManager()
    
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
    
    @property
    def icctransformer(self):
        return ICCTransformerForProfileData(self.icc)
    
    @property
    def lcmsinstance(self):
        return ImageCms.ImageCmsProfile(self.iccfile.file)
    
    def get_profiled_images(self, modl):
        """
        Retrieve ImageModel/ImageWithMetadata subclasses that have
        embedded profile data that matches this ICCModel instances'
        profile. Matches are detected by comparing ICCHashFields.
        """
        modlfield = None
        if modl._meta:
            for field in modl._meta.fields:
                if isinstance(field, ICCHashField):
                    modlfield = getattr(field, 'name', None)
                    break
        
        if modlfield:
            lookup = str('%s__exact' % modlfield)
            if hasattr(modl.objects, 'with_matching_profile'):
                return modl.objects.with_matching_profile(hsh=self.icchash)
            if hasattr(modl.objects, 'with_profile'):
                return modl.objects.with_profile().filter(**{ lookup: self.icchash })
            modl.objects.filter(**{ lookup: self.icchash })
        
        else:
            logg.info("ICCModel.get_profiled_images() failed for model %s -- no ICCHashField defined" % modl.__class__.__name__)
        
        return modl.objects.none()
    
    def save(self, force_insert=False, force_update=False):
        self.modifydate = datetime.now()
        super(ICCModel, self).save(force_insert, force_update)
    
    def __unicode__(self):
        
        if self.icc:
            return u'%s' % (
                self.icc.getDescription(),
            )
        
        return u'-empty-'

"""
South has assuaged me, so I'm happy to assuage it.

"""
try:
    from south.modelsinspector import add_introspection_rules
except ImportError:
    pass
else:
    # 'models inspector' sounds like the punchline of a junior-high-era joke
    add_introspection_rules(
        rules = [
            ((HistogramChannelField,), [], {
                'add_columns': ('add_columns', {}),
            }),
        ], patterns = [
            '^imagekit\.modelfields\.HistogramChannelField',
        ]
    )
    add_introspection_rules(
        rules = [
            ((ICCField,), [], {
            }),
        ], patterns = [
            '^imagekit\.modelfields\.ICCField',
        ]
    )



# Histogram type string map (at the end so we're typesafe)
# XYZHistogram and LabHistogram implementations TBD
HISTOGRAMS = { 'luma': LumaHistogram, 'rgb': RGBHistogram, }



