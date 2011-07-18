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
from colorsys import rgb_to_hls, hls_to_rgb

from imagekit.signals import signalqueue
from imagekit.queue.backends import QueueBase
from imagekit import specs
from imagekit.lib import *
from imagekit.options import Options
from imagekit.modelfields import VALID_CHANNELS, to_matrix
from imagekit.ICCProfile import ICCProfile
from imagekit.utils import logg, img_to_fobj, hexstr
from imagekit.utils import EXIF, ADict, itersubclasses
from imagekit.utils import icchash as icchasher
from imagekit.utils.delegate import DelegateManager, delegate
from imagekit.modelfields import ICCField, ICCHashField, RGBColorField
from imagekit.modelfields import ICCDataField, ICCMetaField, EXIFMetaField
from imagekit.modelfields import HistogramChannelField, Histogram
from imagekit.modelfields import ImageHashField

# Modify image file buffer size.
ImageFile.MAXBLOCK = getattr(settings, 'PIL_IMAGEFILE_MAXBLOCK', 256 * 2 ** 10)

try:
    _storage = getattr(settings, 'IK_STORAGE', None)()
except:
    _storage = FileSystemStorage()
else:
    if not _storage:
        _storage = FileSystemStorage()

# attempt to load haystack
try:
    from haystack.query import SearchQuerySet
except ImportError:
    HAYSTACK = False
else:
    HAYSTACK = True


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
    
    This metaclass parses IKOptions and loads any ImageSpecs it can find in 'spec_module'.
    
    """
    def __init__(cls, name, bases, attrs):
        super(ImageModelBase, cls).__init__(name, bases, attrs)
        parents = [b for b in bases if isinstance(b, ImageModelBase)]
        if not parents:
            return
        
        user_opts = getattr(cls, 'IKOptions', None)
        opts = Options(user_opts)
        
        if opts.spec_module:
            try:
                module = __import__(opts.spec_module,  {}, {}, [''])
            except ImportError:
                raise ImportError('Unable to load imagekit config module: %s' % opts.spec_module)
            
            for spec in module.__dict__.values():
                if isinstance(spec, type):
                    if issubclass(spec, specs.Spec):
                        opts.specs.update({ spec.name(): spec })
        
        # Options.contribute_to_class() won't work unless you do both of these. But... why?
        setattr(cls, '_ik', opts)
        cls.add_to_class('_ik', opts)


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
    
    @property
    def _imgfield(self):
        return getattr(self, self._ik.image_field)
    
    @property
    def _storage(self):
        return getattr(self._ik, 'storage')
    
    @property
    def pilimage(self):
        if self.pk:
            if self._imgfield.name:
                return Image.open(self._storage.open(self._imgfield.name))
        return None
    
    def _dominant(self):
        return self.pilimage.quantize(1).convert('RGB').getpixel((0, 0))
    
    def _mean(self):
        return ImageStat.Stat(self.pilimage.convert('RGB')).mean
    
    def _average(self):
        return self.pilimage.convert('RGB').resize((1, 1), Image.ANTIALIAS).getpixel((0, 0))
    
    def _median(self):
        return reduce((lambda x,y: x[0] > y[0] and x or y), self.pilimage.convert('RGB').getcolors(self.pilimage.size[0] * self.pilimage.size[1]))
    
    def _topcolors(self, numcolors=3):
        if self.pilimage:
            colors = self.pilimage.convert('RGB').getcolors(self.pilimage.size[0] * self.pilimage.size[1])
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
                        map(lambda x: rgb_to_hls(float(x[1][0])/255, float(x[1][1])/255, float(x[1][2])/255), self._topcolors(samplesize)))
                ])[0]
            ))
        except TypeError:
            return ""
    
    def dominanthex(self):
        return hexstr(self._dominant())
    
    def meanhex(self):
        m = self._mean()
        if len(m) == 3:
            return hexstr((int(m[0]), int(m[1]), int(m[2])))
        return hexstr((int(m[0]), int(m[0]), int(m[0])))
    
    def averagehex(self):
        return hexstr(self._average())
    
    def medianhex(self):
        return hexstr(self._median()[1])
    
    def tophex(self, numcolors=3):
        return [hexstr(tc[1]) for tc in self._topcolors(numcolors)]
    
    def save_image(self, name, image, save=True, replace=True):
        if hasattr(image, 'read'):
            data = image.read()
        else:
            data = image
        
        if self._imgfield and replace:
            self._imgfield.delete(save=False)
        
        content = ContentFile(data)
        self._imgfield.save(name, content, save)
    
    def save(self, *args, **kwargs):
        is_new_object = self._get_pk_val() is None
        clear_cache = kwargs.pop('clear_cache', False)
        
        super(ImageModel, self).save(*args, **kwargs)
        
        if is_new_object and self._imgfield:
            clear_cache = False
        
        if clear_cache:
            signalqueue.send_now('clear_cache', sender=self.__class__, instance=self)
        
        #logg.info("About to send the pre_cache signal...")
        return signalqueue.send_now('pre_cache', sender=self.__class__, instance=self)
    
    def clear_cache(self, **kwargs):
        assert self._get_pk_val() is not None, "%s object can't be deleted because its %s attribute is set to None." % (self._meta.object_name, self._meta.pk.attname)
        signalqueue.send_now('clear_cache', sender=self.__class__, instance=self)


class Proof(ImageModel):
    class Meta:
         abstract = False
         verbose_name = "Proof"
         verbose_name_plural = "Proof Images"
    
    class IKOptions:
        spec_module = None
        cache_dir = 'cache'
        proof_dir = 'proofs'
        image_field = 'image'
        storage = _storage
    
    intent_choices = (
        (None,                                      "----"),
        (ImageCms.INTENT_PERCEPTUAL,                "Perceptual"),
        (ImageCms.INTENT_SATURATION,                "Saturation"),
        (ImageCms.INTENT_ABSOLUTE_COLORIMETRIC,     "Absolute Colorimetric"),
        (ImageCms.INTENT_RELATIVE_COLORIMETRIC,     "Relative Colorimetric"),
    )
    
    content_type = models.ForeignKey(ContentType,
        verbose_name="Source Image Type",
        limit_choices_to=dict(
            model__in=(cls.__name__.lower() for cls in itersubclasses(ImageModel))),
        blank=True,
        null=True) # GFK defaults
    
    object_id = models.PositiveIntegerField(verbose_name="Source Image ID",
        db_index=True,
        blank=True,
        null=True) # GFK defaults
    
    sourceimage = generic.GenericForeignKey(
        'content_type',
        'object_id')
    
    sourceprofile = models.ForeignKey('imagekit.ICCModel',
        verbose_name="Source ICC Profile",
        related_name="proofs_as_source",
        on_delete=models.SET_NULL,
        db_index=True,
        editable=True,
        blank=True,
        null=True)
    
    proofprofile = models.ForeignKey('imagekit.ICCModel',
        verbose_name="Proofing ICC Profile",
        related_name="proofs",
        on_delete=models.SET_NULL,
        db_index=True,
        editable=True,
        blank=True,
        null=True)
    
    intent = models.PositiveIntegerField(verbose_name="Render Intent",
        choices=intent_choices,
        default=ImageCms.INTENT_PERCEPTUAL,
        editable=True,
        blank=True,
        null=True)
    
    proofintent = models.PositiveIntegerField(verbose_name="Proof Render Intent",
        choices=intent_choices,
        default=ImageCms.INTENT_ABSOLUTE_COLORIMETRIC,
        editable=True,
        blank=True,
        null=True)
    
    image = models.ImageField(verbose_name="Image",
        storage=_storage,
        null=True,
        blank=True,
        upload_to='images/proofs',
        height_field='h',
        width_field='w',
        max_length=255)
    
    w = models.PositiveIntegerField(verbose_name="width",
        editable=False,
        null=True)
    
    h = models.PositiveIntegerField(verbose_name="height",
        editable=False,
        null=True)
    
    def __init__(self, *args, **kwargs):
        super(Proof, self).__init__(*args, **kwargs)
        
        if self.sourceimage and self.image:
            sourcecls = self.sourceimage.__class__
            
            user_opts = getattr(sourcecls, 'IKOptions', None)
            opts = self._ik
            opts.update(user_opts)
            
            for spec_name, spec in sourcecls._ik.specs.items():
                opts.specs.update({ spec_name: spec })
                
                if issubclass(spec, specs.ImageSpec):
                    prop = specs.FileDescriptor(spec)
                elif issubclass(spec, specs.MatrixSpec):
                    prop = specs.MatrixDescriptor(spec)
                
                opts._props.update({ spec_name: prop })
                propr = opts._props.get(spec_name).accessor(self, opts.specs[spec_name])
                setattr(self, spec_name, propr)
                #self._meta.add_to_class(spec_name, propr)
            
            setattr(self, '_ik', opts)
            #self._meta.add_to_class('_ik', opts)
    
    def _get_targetimage(self):
        return self.image
    def _set_targetimage(self, newimage):
        self.image = newimage
    
    targetimage = property(_get_targetimage, _set_targetimage)
    targetprofile = IK_sRGB
    
    @property
    def targetname(self):
        if self.sourceimage:
            nn = self.sourceimage._imgfield.name
            if nn:
                filepath, basename = os.path.split(str(nn))
                filename, extension = os.path.splitext(basename)
                
                out_filename = "PROOF-" + (self._ik.cache_filename_format % {
                    'filename': filename,
                    'specname': "%s-%s" % (
                        self.proofprofile.icc.getDescription(),
                        self.targetprofile.getDescription(),
                    ),
                    'extension': extension.lstrip('.'),
                })
                
                if callable(self._ik.cache_dir):
                    return self._ik.cache_dir(self, filepath, out_filename)
                else:
                    return os.path.join(self._ik.cache_dir, filepath, out_filename)
        return ''
    
    def generate(self, source=None, reuse_transform=False):
        
        if isinstance(source, ImageModel):
            self.sourceimage = source
            if hasattr(source, 'iccmodel'):
                if source.iccmodel is not None:
                    self.sourceprofile = source.iccmodel
                else:
                    # assume it's sRGB
                    self.sourceprofile = ICCModel.objects.get(icchash__iexact=icchasher(IK_sRGB))
            self.save()
        elif isinstance(source, ICCProfile):
            try:
                matching_icc = ICCModel.objects.get(icchash__iexact=icchasher(source))
            except ObjectDoesNotExist:
                # create a new ICCModel
                new_icc = ICCModel()
                new_icc_file = ContentFile(obj.icc.data)
                new_icc.iccfile.save(
                    new_icc._storage.get_valid_name("%s.icc" % obj.icc.getDescription()),
                    File(new_icc_file),
                )
                new_icc.save()
                self.sourceprofile = new_icc
            else:
                self.sourceprofile = matching_icc
            self.save()
        
        if not hasattr(self, 'prooftransform') or not reuse_transform:
            self.prooftransform = ImageCms.ImageCmsTransform(
                self.sourceprofile.icc.lcmsinstance,
                self.targetprofile.lcmsinstance, # sRGB
                self.sourceimage.pilimage.mode,
                'RGB',
                self.intent,
                proof=self.proofprofile.icc.lcmsinstance,
                proof_intent=self.proofintent,
                flags=ImageCms.FLAGS.get('SOFTPROOFING'),
            )
        
        if self.prooftransform:
            target = self.prooftransform.apply(self.sourceimage.pilimage)
            targetdata = StringIO.StringIO()
            target.save(targetdata, format=self.sourceimage.pilimage.format)
            targetdata.seek(0)
            
            if self.targetname:
                self.save_image(
                    self.targetname,
                    targetdata,
                    save=True,
                    replace=True)
            
            else:
                logg.warning("*** Not saving a perfectly good proofed image due to the lack of a targetname.")
    
    def __repr__(self):
        pk = self.pk or '-nil-'
        src = self.sourceprofile and self.sourceprofile.icc.getDescription() or '-src-'
        prf = self.proofprofile and self.proofprofile.icc.getDescription() or '-PRF-'
        dst = self.targetprofile and self.targetprofile.getDescription() or '-dst-'
        return "<imagekit.Proof #%s %s>" % (self.pk, [src,prf,dst])


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
    
    L = HistogramChannelField(channel='L', verbose_name="Luma",
        pil_reference=lambda instance: instance.pilimage.convert('L'))

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
    def with_profile(self):
        return self.filter(icc__isnull=False)
    
    @delegate
    def with_exif(self):
        return self.filter(exif__isnull=False)
    
    @delegate
    def matching_profile(self, icc=None, hsh=None):
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
    def discordant_profile(self, icc=None, hsh=None):
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
    
    # We can sort by these color values.
    dominantcolor = RGBColorField(verbose_name="Dominant Color",
        extractor=lambda instance: instance.dominanthex())
    
    meancolor = RGBColorField(verbose_name="Mean Color",
        extractor=lambda instance: instance.meanhex())
    
    averagecolor = RGBColorField(verbose_name="Average Color",
        extractor=lambda instance: instance.averagehex())
    
    mediancolor = RGBColorField(verbose_name="Median Color",
        extractor=lambda instance: instance.medianhex())
    
    # EXIF image metadata
    exif = EXIFMetaField(verbose_name="EXIF data",
        storage=_storage,
        editable=True,
        blank=True,
        null=True)
    
    # ICC color management profile data
    icc = ICCMetaField(verbose_name="ICC data",
        hash_field='icchash',
        editable=False,
        null=True)
    
    # Unique hash of ICC profile data (for fast DB searching)
    icchash = ICCHashField(verbose_name="ICC embedded profile hash",
        unique=False, # ICCHashField defaults to unique=True
        editable=True,
        blank=True,
        null=True)
    
    # Unique hash of the image data
    imagehash = ImageHashField(verbose_name="Image data hash",
        editable=True)
    
    def proofimage(self, proofprofile, sourceprofile=None, **kwargs):
        
        if sourceprofile is None:
            if self.iccmodel:
                sourceprofile = self.iccmodel
        
        proof = Proof(
            content_type=self.content_type,
            object_id=self.pk,
            #sourceimage=self,
            sourceprofile=sourceprofile,
            proofprofile=proofprofile,
        )
        
        if 'intent' in kwargs:
            proof.intent = kwargs.pop('intent')
        
        if 'proofintent' in kwargs:
            proof.proofintent = kwargs.pop('proofintent')
        
        return proof
    
    @property
    def content_type(self):
        return ContentType.objects.get_for_model(self.__class__)
    
    @property
    def iccmodel(self):
        try:
            return ICCModel.objects.get(icchash=self.icchash)
        except ICCModel.DoesNotExist:
            return None
    
    @property
    def same_profile_set(self):
        return self.__class__.objects.matching_profile(hsh=self.icchash)
    
    @property
    def different_profile_set(self):
        return self.__class__.objects.discordant_profile(hsh=self.icchash)
    
    @property
    def icctransformer(self):
        return self.icc.transformer
    
    def __repr__(self):
        return "<%s #%s>" % (self.__class__.__name__, self.pk)


class ICCQuerySet(models.query.QuerySet):
    
    def __init__(self, *args, **kwargs):
        super(ICCQuerySet, self).__init__(*args, **kwargs)
        random.seed()
    
    @delegate
    def rnd(self):
        return random.choice(self.all())
    
    @delegate
    def profile_match(self, icc=None, hsh=None):
        if icc:
            if hasattr(icc, 'data'):
                hsh = hashlib.sha1(icc.data).hexdigest()
        if hsh:
            return self.get(
                icc__isnull=False,
                icchash__exact=hsh,
            )
        return None
    
    @delegate
    def profile_search(self, search_string='', sqs=False):
        """
        Arbitrarily searches the Haystack index of profile metadata, if it's available.
        """
        if HAYSTACK and search_string:
            if not hasattr(self, 'srcher'):
                self.srcher = SearchQuerySet().models(self.model)
            
            results = self.srcher.auto_query(search_string)
            
            if sqs:
                # return the SearchQuerySet if we were asked for it explicitly
                return results
            else:
                # default to constructing a QuerySet from the IDs we got
                return self.filter(pk__in=(result.object.pk for result in results))
        
        if not HAYSTACK:
            logg.warning("ICCQuerySet.profile_search() Haystack Search isn't configured -- not filtering profiles (q='%s')." % search_string)
        
        return self.all()

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
        return self.icc.transformer
    
    @property
    def lcmsinstance(self):
        return ImageCms.ImageCmsProfile(self.iccfile.file)
    
    def get_profiled_images(self, modl):
        """
        Retrieve ImageModel/ImageWithMetadata subclasses that have
        embedded profile data that matches this ICCModel instances'
        profile. Matches are detected by comparing ICCHashFields.
        
        """
        # use model's with_matching_profile shortcut call, if present
        if hasattr(modl.objects, 'matching_profile'):
            return modl.objects.matching_profile(hsh=self.icchash)
        
        # no with_matching_profile shortcut; scan fields for an ICCProfileHash
        modlfield = None
        if modl._meta:
            for field in modl._meta.fields:
                if isinstance(field, ICCHashField):
                    modlfield = getattr(field, 'name', None)
                    break
        
        if modlfield:
            lookup = str('%s__exact' % modlfield)
            if hasattr(modl.objects, 'with_profile'):
                # limit query to model instances with profiles, if possible
                return modl.objects.with_profile().filter(**{ lookup: self.icchash })
            modl.objects.filter(**{ lookup: self.icchash })
        
        else:
            logg.info("ICCModel.get_profiled_images() failed for model %s -- no ICCHashField defined and no profile hash lookup methods found" % modl.__class__.__name__)
        
        return modl.objects.none()
    
    def save(self, force_insert=False, force_update=False, **kwargs):
        self.modifydate = datetime.now()
        super(ICCModel, self).save(force_insert, force_update, **kwargs)
    
    def __unicode__(self):
        
        if self.icc:
            return u'%s' % (
                self.icc.getDescription(),
            )
        
        return u'-empty-'


class SignalQuerySet(models.query.QuerySet):
    """
    SignalQuerySet is a QuerySet that works as an ImageKit queue backend.
    
    The actual QueueBase override methods are implemented here and delegated to
    SignalManager, which is a DelegateManager subclass with the QueueBase
    implementation "mixed in".
    
    Since you can't nakedly instantiate managers outside of a model
    class, we use a proxy class to hand off SignalQuerySet's delegated
    manager to the queue config stuff. See the working implementation in
    imagekit.queue.backends.DatabaseQueueProxy for details.
    
    """
    @delegate
    def queued(self, enqueued=True):
        return self.filter(queue_name=self.queue_name, enqueued=enqueued).order_by("createdate")
    
    @delegate
    def ping(self):
        return True
    
    @delegate
    def push(self, value):
        return self.get_or_create(queue_name=self.queue_name, value=value, enqueued=True)
    
    @delegate
    def pop(self):
        """
        Dequeued signals are marked as such (but not deleted) by default.
        """
        out = self.queued()[0]
        out.enqueued = False
        out.save()
        return str(out.value)
    
    def count(self, enqueued=True):
        """
        This override can't be delegated as the super() call isn't portable.
        """
        return super(self.__class__, self.all().queued(enqueued=enqueued)).count()
    
    @delegate
    def clear(self):
        self.queued().update(enqueued=False)
    
    @delegate
    def values(self, floor=0, ceil=-1):
        if floor < 1:
            floor = 0
        if ceil < 1:
            ceil = self.count()
        
        out = self.queued()[floor:ceil]
        return [str(value[0]) for value in out.values_list('value')]

class SignalManager(DelegateManager, QueueBase):
    __queryset__ = SignalQuerySet
    
    def __init__(self, *args, **kwargs):
        QueueBase.__init__(self, *args, **kwargs)
        DelegateManager.__init__(self, *args, **kwargs)
    
    def count(self, enqueued=True):
        return self.queued(enqueued=enqueued).count()
    
    def _get_queue_name(self):
        if self._queue_name:
            return self._queue_name
        return None
    
    def _set_queue_name(self, queue_name):
        self._queue_name = queue_name
        self.__queryset__.queue_name = queue_name
    
    queue_name = property(_get_queue_name, _set_queue_name)

class EnqueuedSignal(models.Model):
    class Meta:
        abstract = False
        verbose_name = "Enqueued Signal"
        verbose_name_plural = "Enqueued Signals"
    
    objects = SignalManager()
    
    enqueued = models.BooleanField("Enqueued",
        default=True,
        editable=True)
    
    queue_name = models.CharField(verbose_name="Queue name",
        default="default",
        unique=False,
        blank=True,
        max_length=255, db_index=True)
    
    value = models.TextField(verbose_name='Serialized signal value',
        editable=False,
        unique=True, db_index=True,
        blank=True,
        null=True)
    
    createdate = models.DateTimeField('Created on',
        default=datetime.now,
        blank=True,
        editable=False)
    
    def __repr__(self):
        if self.value:
            return str(self.value)
        return "{'instance':null}"
    
    def __unicode__(self):
        if self.value:
            return unicode(self.value)
        return u"{'instance':null}"


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



