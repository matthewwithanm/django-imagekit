import base64, hashlib, numpy, uuid
from django.db import models
from django.db.models import fields
from django.db.models.fields import files
from django.db.models import signals
from django.utils.translation import ugettext_lazy, ugettext as _
from django.core.files import File
from django.core.exceptions import MultipleObjectsReturned
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from ICCProfile import ICCProfile
from jogging import logging as logg
import imagekit.models


"""
When declaring HistogramChannelFields and Histograms, their respective channel
or colorspace type has do be one from these tuples here (for the moment).
See the fields' individual implementation notes below for details.

"""

VALID_CHANNELS = (
    'L',                    # luminance
    'R', 'G', 'B',          # RGB
    'A', 'a',               # alpha (little-a for premultiplied)
    'C', 'M', 'Y', 'K',     # CMYK
)

VALID_COLORSPACES = (
    "Luma",                 # 1 8-bit channel
    "RGB",                  # 3 8-bit channels
)


# Blatant misnomer, returning an array -- but so whatevs, the point is that
# it provides consistent return types when accessing HistogramChannelField data.
to_matrix = lambda l: numpy.array(l, dtype=int)


class ICCDataField(models.TextField):
    """
    Model field representing an ICC profile instance.
    
    Represented in python as an ICCProfile instance -- see ICCProfile.py for details.
    The profile itself is stored in the database as unicode data. I haven't had any
    problems cramming fairly large profiles (>2 megs) into postgres; let me know if
    your backend chokes on profiles you throw its way.
    
    Example usage:
    -------------------------
    
    from django.db import models
    import imagekit.models
    import imagekit.modelfields
    from imagekit.ICCProfile import ICCProfile
    
    class ImageWithProfile(imagekit.models.ImageModel):
        class IKOptions:
            spec_module = ...
            image_field = 'image'
        image = models.ImageField( ... )
        iccdata = imagekit.modelfields.ICCDataField(editable=False, null=True)
        
        def save(self, force_insert=False, force_update=False):
            if self.pilimage:
                if self.pilimage.info.get('icc_profile'):
                    self.iccdata = ICCProfile(self.pilimage.info['icc_profile'])
            super(ImageWithProfile, self).save(force_insert, force_update)
    
    -------------------------
    
    >>> from myapp.models import ImageWithProfile
    >>> axim = ImageWithProfile.objects.all()[0]
    >>> axim.iccdata.calculateID()
    "\xd95\xa4/\x04\xcf'\xa2\xd9\xf2\x17\x97\xd5\x0c\xf2j"
    >>> axim.iccdata.getIDString
    '2TWkLwTPJ6LZ8heX1Qzyag=='
    >>> axim.iccdata.getCopyright()
    u'Copyright (c) 1998 Hewlett-Packard Company'
    >>> axim.iccdata.getDescription()
    u'sRGB IEC61966-2.1'
    >>> axim.iccdata.getViewingConditionsDescription()
    u'Reference Viewing Condition in IEC61966-2.1'
    
    -------------------------
    
    """
    __metaclass__ = models.SubfieldBase
    
    def to_python(self, value):
        """
        Always return a valid ICCProfile instance, or None.
        """
        if value:
            if isinstance(value, ICCProfile):
                return value
            return ICCProfile(base64.b64decode(value))
        return None
    
    def get_prep_value(self, value):
        """
        Always return the profile data as a string, or an empty string.
        """
        if value:
            if isinstance(value, ICCProfile):
                return value.data
            if len(value) > 0:
                return value
        return value
    
    def get_db_prep_value(self, value, connection, prepared=False):
        """
        Always return a valid unicode data string.
        """
        if not prepared:
            value = self.get_prep_value(value)
        if value:
            return base64.b64encode(value)
        return value
    
    def value_to_string(self, obj):
        """
        Return unicode data (for now) suitable for serialization (JSON, pickle, etc)
        """
        return self.get_db_prep_value(self._get_val_from_obj(obj))
    
    def south_field_triple(self):
        """
        Represent the field properly to the django-south model inspector.
        See also: http://south.aeracode.org/docs/extendingintrospection.html
        """
        from south.modelsinspector import introspector
        args, kwargs = introspector(self)
        return ('imagekit.models.ICCDataField', args, kwargs)


class ICCMetaField(ICCDataField):
    """
    This ICCDataField subclass will automatically refresh itself
    with ICC data it finds in the image classes' PIL instance. The
    methods it impelemnts are designed to work with the ImageWithMetadata
    abstract base class to accomplish this feat, using signals. 
    """
    
    def __init__(self, *args, **kwargs):
        self.pil_reference = kwargs.pop('pil_reference', 'pilimage')
        super(ICCMetaField, self).__init__(*args, **kwargs)
    
    def contribute_to_class(self, cls, name):
        if not hasattr(self, 'db_column'):
            self.db_column = name
        if not hasattr(self, 'verbose_name'):
            self.verbose_name = name
        super(ICCMetaField, self).contribute_to_class(cls, name)
        
        #print("About to connect (%s)" % cls.__name__)
        signals.pre_save.connect(self.refresh_icc_data, sender=cls)
    
    def refresh_icc_data(self, **kwargs): # signal, sender, instance
        """
        Stores ICC profile data in the field before saving.
        """
        logg.info("refresh_icc_data() called...")
        
        instance = kwargs.get('instance')
        
        try:
            image = instance.image
            pil_reference = self.pil_reference
            
            if callable(pil_reference):
                pilimage = pil_reference(image)
            else:
                pilimage = getattr(image, pil_reference, 'pilimage')
        
        except AttributeError, err:
            logg.warning("*** Couldn't refresh ICC data with custom callable (AttributeError was thrown: %s)" % err)
            return
        except TypeError, err:
            logg.warning("*** Couldn't refresh ICC data with custom callable (TypeError was thrown: %s)" % err)
            return
        except IOError, err:
            logg.warning("*** Couldn't refresh ICC data with custom callable (IOError was thrown: %s)" % err)
            return
        
        profile_string = ''
        
        if pilimage:
            try:
                profile_string = pilimage.info.get('icc_profile', '')
            except:
                logg.info("Exception was raised when trying to get the icc profile string")
            
            if len(profile_string):
                logg.info("Saving icc profile for %s %s ..." % (instance.__class__.__name__, instance.id))
                instance.icc = ICCProfile(profile_string)
                logg.info("Saved icc profile '%s' for %s" % (instance.icc.getDescription(), instance.id))
    
    def south_field_triple(self):
        """
        Represent the field properly to the django-south model inspector.
        See also: http://south.aeracode.org/docs/extendingintrospection.html
        """
        from south.modelsinspector import introspector
        args, kwargs = introspector(self)
        return ('imagekit.models.ICCMetaField', args, kwargs)


class HistogramColumn(models.IntegerField):
    """
    Model field representing an integer column in an 8-bit image histogram.
    
    You don't create these yourself; they are added automatically
    to a histogram model's definition when you set that model up
    as a subclass of HistogramBase and attach some HistogramChannelFields.
    
    See the HistogramChannelField implementation and notes below, and also
    the HistogramBase model in models.py for more.
    
    """
    __metaclass__ = models.SubfieldBase
    
    def __init__(self, *args, **kwargs):
        self.channel = kwargs.pop('channel', None)
        if self.channel:
            kwargs.setdefault('default', -1)
            kwargs.setdefault('editable', True)
            kwargs.setdefault('blank', False)
            kwargs.setdefault('null', False)
        else:
            raise TypeError("Can't create a HistogramColumn without specifying a channel.")
        super(HistogramColumn, self).__init__(*args, **kwargs)
    
    def south_field_triple(self):
        """
        Represent the field properly to the django-south model inspector.
        See also: http://south.aeracode.org/docs/extendingintrospection.html
        """
        from south.modelsinspector import introspector
        args, kwargs = introspector(self)
        return ('django.db.models.IntegerField', args, kwargs)


class HistogramChannelDescriptor(object):
    """
    Histogram channel descriptor for accessing the histogram channel data through the 
    field referring to the histogram.
    Implementation is derived from django.db.models.fields.files.FileDescriptor.
    """
    
    def __init__(self, field):
        self.field = field
    
    def __get__(self, instance=None, owner=None):
        if instance is None:
            raise AttributeError(
                "The '%s' attribute can only be accessed from %s instances."
                % (self.field.name, owner.__name__))
        
        histogram_channel = instance.__dict__[self.field.original_channel]
        
        if isinstance(histogram_channel, (numpy.matrixlib.matrix, numpy.ndarray)):
            if not issubclass(histogram_channel.dtype, int):
                return histogram_channel.astype(int)
            return histogram_channel
        
        elif isinstance(histogram_channel, (list, tuple)):
            return to_matrix(histogram_channel)
        
        # get the fucking histogram channel data out of the database here
        elif isinstance(histogram_channel, (basestring, type(None))):
            out = []
            if int(getattr(instance, "__%s_00" % histogram_channel)) < 0:
                instance.save() # refresh and save
            
            if histogram_channel:
                for i in xrange(256):
                    histocolname = "__%s_%02X" % (histogram_channel, i)
                    out.append(getattr(instance, histocolname))
            return to_matrix(out)
        
        else:
            # not sure what this is, let's try to make it a list:
            try:
                return to_matrix(list(histogram_channel))
            except TypeError:
                return to_matrix([])
    
    def __set__(self, instance, value):
        instance.__dict__[self.field.name] = value

class HistogramChannelField(models.CharField):
    """
    Model field representing a single 8-bit channel in an image histogram.
    For use with companded 8-bit colorspaces, such as sRGB and friends;
    CMYK, named colorspaces, and linear spaces like Lab and XYZ
    will need their own HistogramColumn and HistogramChannelField implementations
    that specifically support these colorspaces' numerical representations.
    
    The HistogramBase model uses this field. If you want to define a histogram
    for a colorspace -- something done infrequently -- you can put it together
    out of HistogramChannelFields like so:
    
    class TetrachromaticHistogram(HistogramBase):
        # Since so far tetrachromacity has only been
        # observed in women, you'll want to implement
        # this if you want to claim sec. 508 compliance.
        R = HistogramChannelField(channel='R', verbose_name="Red")
        G = HistogramChannelField(channel='G', verbose_name="Green")
        B = HistogramChannelField(channel='B', verbose_name="Blue")
        U = HistogramChannelField(channel='U', verbose_name="Low Wavelengths My Cursed Male Eyes Can't See")
    
    At the moment, you also would have to amend the VALID_CHANNELS constant
    defined immediately above; in this case 'channels' are used to properly
    namespace the hidden HistogramColumn fields generated when you define
    a HistogramChannelField on a HistogramBase subclass at the moment and making
    your own shit up in the 'channels' kwarg will wind up in your database.
    The arrangement with VALID_CHANNELS will go away in the future (just like
    all specious architectural decisions in eveyone's code everywhere.)
    
    """
    
    def __init__(self, channel="L", *args, **kwargs):
        # see https://bitbucket.org/carljm/django-markitup/src/tip/markitup/fields.py
        self.pil_reference = kwargs.pop('pil_reference', 'pilimage')
        self.add_columns = not kwargs.pop('add_columns', False)
        
        for arg in ('primary_key', 'unique'):
            if arg in kwargs:
                raise TypeError("'%s' is not a valid argument for %s." % (arg, self.__class__))
        if channel not in VALID_CHANNELS:
            raise TypeError("Invalid channel type %s was specified for HistogramChannelField" % channel)
        self.channel = self.original_channel = channel
        
        kwargs['max_length'] = 1
        kwargs.setdefault('default', channel)
        kwargs.setdefault('verbose_name', "8-bit Histogram Channel")
        kwargs.setdefault('max_length', 1)
        kwargs.setdefault('editable', True)
        kwargs.setdefault('blank', False)
        kwargs.setdefault('null', False)
        super(HistogramChannelField, self).__init__(*args, **kwargs)
    
    def get_internal_type(self):
        return "CharField"
    
    def get_prep_lookup(self, lookup_type, value):
        return super(HistogramChannelField, self).get_prep_lookup(self.original_channel)
    
    def get_prep_value(self, value):
        return unicode(self.original_channel)
    
    def contribute_to_class(self, cls, name):
        if not hasattr(self, 'db_column'):
            self.db_column = name
        if not hasattr(self, 'verbose_name'):
            self.verbose_name = name
        super(HistogramChannelField, self).contribute_to_class(cls, name)
        
        setattr(cls, self.original_channel, HistogramChannelDescriptor(self))
        signals.pre_save.connect(self.refresh_histogram_channel, sender=cls)
        
        if self.add_columns and not cls._meta.abstract:
            if hasattr(self, 'original_channel'):
                for i in xrange(256):
                    histocol = HistogramColumn(channel=self.original_channel)
                    histocolname = "__%s_%02X" % (self.original_channel, i)
                    histocol.db_column = histocolname
                    histocol.verbose_name = histocolname
                    self.creation_counter = histocol.creation_counter + 1
                    cls.add_to_class(histocolname, histocol)
    
    def refresh_histogram_channel(self, **kwargs):
        """
        Stores histogram column values in their respective db fields before saving
        """
        instance = kwargs.get('instance')
        image = instance.image
        
        pil_reference = self.pil_reference
        
        try:
            if callable(pil_reference):
                pilimage = pil_reference(image)
            else:
                pilimage = getattr(image, pil_reference, 'pilimage')
        
        except AttributeError, err:
            logg.warning("*** Couldn't refresh histogram channel '%s' with custom callable (AttributeError was thrown: %s)" % (self.original_channel, err))
            return
        except TypeError, err:
            logg.warning("*** Couldn't refresh histogram channel '%s' with custom callable (TypeError was thrown: %s)" % (self.original_channel, err))
            return
        except IOError, err:
            logg.warning("*** Couldn't refresh histogram channel '%s' with custom callable (IOError was thrown: %s)" % (self.original_channel, err))
            return
        
        if pilimage:
            if self.original_channel in pilimage.mode:
                channel_data = pilimage.split()[pilimage.mode.index(self.original_channel)].histogram()[:256]
                for i in xrange(256):
                    histocolname = "__%s_%02X" % (self.original_channel, i)
                    setattr(instance, histocolname, int(channel_data[i]))
                logg.info("Refreshed '%s' histogram." % self.original_channel)
    
    def save_form_data(self, instance, data):
        """
        Not sure about this one.
        """
        if data:
            setattr(instance, self.channel, data)
    
    def south_field_triple(self):
        """
        Represent the field properly to the django-south model inspector.
        See also: http://south.aeracode.org/docs/extendingintrospection.html
        """
        from south.modelsinspector import introspector
        args, kwargs = introspector(self)
        return ('imagekit.modelfields.HistogramChannelField', args, kwargs)

class HistogramDescriptor(object):
    """
    Histogram descriptor for accessing an instance of a HistogramBase subclass through the 
    referrent field.
    Implementation is derived from django.db.models.fields.files.FileDescriptor.
    """
    
    def __init__(self, field):
        self.field = field
    
    def __get__(self, instance=None, owner=None):
        if instance is None:
            raise AttributeError(
                "The '%s' attribute can only be accessed from %s instances."
                % (self.field.name, owner.__name__))
        
        histogram_field = instance.__dict__[self.field.name]
        
        if isinstance(histogram_field, imagekit.models.HistogramBase):
            return histogram_field
        
        elif isinstance(histogram_field, (basestring, type(None))):
            # get a histogram instance, or create a new one
            histogram_rel_name = '_%s_histogram_relation' % self.field.original_colorspace.lower()
            histogram_rel = getattr(instance, histogram_rel_name, None)
            
            if not histogram_rel:
                raise AttributeError("No histogram relation found for %s" % instance)
            
            try:
                return histogram_rel.get()
            except ObjectDoesNotExist:
                ThisHistogramClass = imagekit.models.HISTOGRAMS.get(self.field.original_colorspace.lower(), None)
                return ThisHistogramClass(imagewithmetadata=instance)
        
        else:
            # not sure what this is
            logg.info("WTF is this: %s" % histogram_field)
            return histogram_field
    
    def __set__(self, instance, value):
        instance.__dict__[self.field.name] = value

class Histogram(fields.CharField):
    """
    Field to refer to a HistogramBase model and provide access to the appropriate
    instances and callbacks.
    
    HistogramBase uses a django GenericForeignKey to refer to the image from
    which histogram implementations -- subclasses of HistogramBase -- derive
    their data. Since you can't stick a GenericRelation field onto an
    abstract base model like ImageWithMetadata, we have this field selectively
    contribute one. 
    
    Also, it makes things nicer for other ImageKit programmers -- potentially,
    for colorspaces with specific needs, they could just be like:
    
    class IWorkInTelevisionButIPaintOnTheWeekends(ImageWithMetadata):
        # I haven't implemented these
        ccir601 = Histogram("YUV")
        pigments = Histogram("RYB")
    
    Like HistogramChannelField does with its channel flags, it checks the colorspace kwarg
    against a constant, VALID_COLORSPACES.
    
    """
    
    def __init__(self, colorspace="Luma", *args, **kwargs):
        for arg in ('primary_key', 'unique'):
            if arg in kwargs:
                raise TypeError("'%s' is not a valid argument for %s." % (arg, self.__class__))
        if colorspace not in VALID_COLORSPACES:
            raise TypeError("Invalid colorspace type %s was specified for Histogram" % colorspace)
        self.colorspace = self.original_colorspace = colorspace
        kwargs['max_length'] = 10
        kwargs.setdefault('default', colorspace)
        kwargs.setdefault('verbose_name', "8-bit Image Histogram")
        kwargs.setdefault('max_length', 10)
        kwargs.setdefault('editable', True)
        kwargs.setdefault('blank', False)
        kwargs.setdefault('null', False)
        super(Histogram, self).__init__(*args, **kwargs)
    
    def get_internal_type(self):
        return "CharField"
    
    def get_prep_lookup(self, lookup_type, value):
        return super(Histogram, self).get_prep_lookup(self.original_colorspace)
    
    def get_prep_value(self, value):
        return unicode(self.original_colorspace)
    
    def contribute_to_class(self, cls, name):
        super(Histogram, self).contribute_to_class(cls, name)
        if not cls._meta.abstract:
            setattr(cls, self.name, HistogramDescriptor(self))
            signals.pre_save.connect(self.save_related_histogram, sender=cls)
            
            histogram = generic.GenericRelation(imagekit.models.HISTOGRAMS.get(self.original_colorspace.lower()))
            histogram.verbose_name = "Related %s Histogram" % self.original_colorspace
            histogram.related_name = '_%s_histogram_relation' % self.original_colorspace.lower()
            self.creation_counter = histogram.creation_counter + 1
            cls.add_to_class('_%s_histogram_relation' % self.original_colorspace.lower(), histogram)
    
    def save_related_histogram(self, **kwargs): # signal, sender, instance
        """
        Saves a histogram when its related ImageWithMetadata object is about to be saved.
        
        """
        instance = kwargs.get('instance')
        logg.info("-- About to try and wring histograms out of '%s'." % getattr(instance, 'pk', str(instance)))
        
        histogram_type = self.original_colorspace.lower()
        if hasattr(instance, "histogram_%s" % histogram_type):
            related_histogram = getattr(instance, "histogram_%s" % histogram_type, None)
            
            if related_histogram:
                related_histogram.save()
            
            else:
                logg.info("--X DID NOT SAVE A HISTOGRAM OF ANY TYPE (much less '%s') -- RelatedHistogramClass came up NoneType" % histogram_type.upper())
        
        else:
            logg.info("--X an ImageWithMetadata subclass didn't have a property for histogram (type '%s') for some reason, so we did no save." % histogram_type.upper())
    
    def south_field_triple(self):
        """
        Represent the field properly to the django-south model inspector.
        See also: http://south.aeracode.org/docs/extendingintrospection.html
        """
        from south.modelsinspector import introspector
        args, kwargs = introspector(self)
        return ('imagekit.modelfields.Histogram', args, kwargs)
    
    

class ICCHashField(fields.CharField):
    """
    Store the sha1 of the ICC profile file we're talking about.
    
    ICCHashField is used to uniquely identify ICCModel instances, which are stored
    as database-tracked files, a la django's ImageField -- you can't just use
    unique=True because when we mean 'unique', we mean the binary contents of the
    file and not the path, which is a problem ICCDataField doesn't have; calculating
    the hash dynamically might sound fine until you have an archive of 10,000 ICC files
    on s3, in which case you will want to avoid opening up and hashing everything
    whenever you hit save in the admin (or what have you).
    
    """
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('db_index', True)
        kwargs.setdefault('max_length', 40)
        kwargs.setdefault('editable', False)
        kwargs.setdefault('unique', True)
        kwargs.setdefault('blank', True)
        kwargs.setdefault('null', True)
        super(ICCHashField, self).__init__(*args, **kwargs)
    
    def south_field_triple(self):
        """
        Represent the field properly to the django-south model inspector.
        See also: http://south.aeracode.org/docs/extendingintrospection.html
        """
        from south.modelsinspector import introspector
        args, kwargs = introspector(self)
        return ('imagekit.models.ICCHashField', args, kwargs)

"""
FileField subclasses for ICC profile documents.

Each of the following fields and helpers are subclassed from django's FileField components;
I derived all of them from reading the code morsels that implement django ImageFileFields;
they're well-commented, so if any of this confuses you, read that stuff -- it's in and around
django.db.models.fields.images I believe.

"""
class ICCFile(File):
    """
    django.core.files.File subclass with ICC profile support.
    """
    def _load_icc_file(self):
        if not hasattr(self, "_profile_cache"):
            close = self.closed
            self.open()
            pos = self.tell()
            dat = self.read()
            hsh = hashlib.sha1(dat).hexdigest()
            
            self._profile_cache = (ICCProfile(profile=dat), hsh)
            
            if close:
                self.close()
            else:
                self.seek(pos)
        return self._profile_cache
    
    def _get_iccdata(self):
        return self._load_icc_file()[0]
    iccdata = property(_get_iccdata)
    
    def _get_hsh(self):
        return self._load_icc_file()[1]
    hsh = property(_get_hsh)

class ICCFileDescriptor(files.FileDescriptor):
    """
    django.db.models.fields.files.FileDescriptor subclass with ICC profile support.
    """
    def __set__(self, instance, value):
        previous_file = instance.__dict__.get(self.field.name)
        super(ICCFileDescriptor, self).__set__(instance, value)
        if previous_file is not None:
            self.field.update_data_fields(instance, force=True)

class ICCFieldFile(ICCFile, files.FieldFile):
    """
    django.db.models.fields.files.FileDescriptor subclass with ICC profile support.
    """
    def delete(self, save=True):
        if hasattr(self, '_profile_cache'):
            del self._profile_cache
        super(ICCFieldFile, self).delete(save)

class ICCField(files.FileField):
    """
    django.db.models.fields.files.FileField subclass with ICC profile support.
    """
    attr_class = ICCFieldFile
    descriptor_class = ICCFileDescriptor
    description = ugettext_lazy("ICC file path")
    
    def __init__(self, verbose_name=None, name=None, data_field=None, hash_field=None, add_rendered_field=False, **kwargs):
        self.data_field = data_field
        self.hash_field = hash_field
        self.__class__.__base__.__init__(self, verbose_name, name, **kwargs)
    
    def contribute_to_class(self, cls, name):
        super(ICCField, self).contribute_to_class(cls, name)
        signals.post_init.connect(self.update_data_fields, sender=cls, dispatch_uid=uuid.uuid4().hex)
    
    def update_data_fields(self, instance, force=False, *args, **kwargs):
        has_data_fields = self.data_field or self.hash_field
        if not has_data_fields:
            return
        
        ffile = getattr(instance, self.attname)
        if not ffile and not force:
            return
        
        data_fields_filled = not(
            (self.data_field and not getattr(instance, self.data_field))
            or (self.hash_field and not getattr(instance, self.hash_field))
        )
        if data_fields_filled and not force:
            return
        
        try:
            if ffile:
                if ffile.iccdata:
                    iccdata = ffile.iccdata
                else:
                    iccdata = None
                if ffile.hsh:
                    hsh = ffile.hsh
                else:
                    hsh = None
            else:
                iccdata = None
                hsh = None
        except ValueError:
            iccdata = None
            hsh = None
        
        if self.data_field:
            setattr(instance, self.data_field, iccdata)
        if self.hash_field:
            setattr(instance, self.hash_field, hsh)
        
        def south_field_triple(self):
            """
            Represent the field properly to the django-south model inspector.
            See also: http://south.aeracode.org/docs/extendingintrospection.html
            """
            from south.modelsinspector import introspector
            args, kwargs = introspector(self)
            return ('imagekit.modelfields.ICCField', args, kwargs)

"""
South has assuaged me, so I'm happy to assuage it.

"""
try:
    from south.modelsinspector import add_introspection_rules
except ImportError:
    pass
else:
    add_introspection_rules(
        rules = [
            ((HistogramChannelField,), [], {
                'add_columns': ('add_columns', {}),
            }),
        ], patterns = [
            '^imagekit\.modelfields\.HistogramChannelField',
        ]
    )





