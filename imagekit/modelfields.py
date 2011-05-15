import base64, numpy, uuid
from django.db import models
from django.db.models import fields
from django.db.models.fields import files
from django.db.models import signals
from ICCProfile import ICCProfile
from jogging import logging as logg


class ICCDataField(models.TextField):
    """
    Model field representing an ICC profile instance.
    
    Represented in python as an ICCProfile instance -- see ICCProfile.py for details.
    Stored in the database as unicode data.
    
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
        return ('django.db.models.TextField', args, kwargs)

class ICCMetaField(ICCDataField):
    
    def contribute_to_class(self, cls, name):
        if not hasattr(self, 'db_column'):
            self.db_column = name
        if not hasattr(self, 'verbose_name'):
            self.verbose_name = name
        super(ICCMetaField, self).contribute_to_class(cls, name)
        
        #print("About to connect (%s)" % cls.__name__)
        signals.pre_save.connect(ICCMetaField.refresh_icc_data, sender=cls, dispatch_uid=uuid.uuid4().hex)
    
    @classmethod
    def refresh_icc_data(cls, **kwargs): # signal, sender, instance
        """
        Stores ICC profile data in the field before saving.
        """
        instance = kwargs.get('instance')
        pilimage = getattr(instance, 'pilimage', None)
        profile_string = ''
        
        if pilimage:
            #logg.info("About to attempt to refresh ICC data (%s)" % kwargs)
            try:
                profile_string = pilimage.info.get('icc_profile', '')
            except:
                logg.info("Exception was raised when trying to get the icc profile string")
            
            if len(profile_string):
                #logg.info("Saving icc profile for %s %s ..." % (instance.__class__.__name__, instance.id))
                instance.icc = ICCProfile(profile_string)
                #logg.info("Saved icc profile '%s' for %s" % (instance.icc.getDescription(), instance.id))

class HistogramColumn(models.IntegerField):
    """
    Model field representing a column in an image histogram.
    See the Histogram model (and subclasses) in models.py for the implementation.
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

class HistogramDescriptor(object):
    """
    Histogram descriptor for accessing the histogram data through the 
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
        
        to_matrix = lambda l: numpy.matrix(l, dtype=numpy.uint9)
        histogram = instance.__dict__[self.field.name]
        
        if isinstance(histogram, (numpy.array, numpy.matrix)):
            if not issubclass(histogram.dtype, numpy.uint8):
                return histogram.astype(numpy.uint8)
            return histogram
        
        elif isinstance(histogram, (list, tuple)):
            return to_matrix(histogram)
        
        elif isinstance(histogram, (basestring, type(None))):
            # get the fucking histogram out of the database here
            out = []
            if histogram:
                for i in xrange(256):
                    histocolname = "__%s_%02X" % (histogram, i)
                    out.append(getattr(instance, histocolname))
            return to_matrix(out)
        
        else:
            # not sure what this is, let's try to make it a list:
            try:
                return to_matrix(list(histogram))
            except TypeError:
                return to_matrix([])
    
    def __set__(self, instance, value):
        instance.__dict__[self.field.name] = value

VALID_CHANNELS = (
    'L',                    # luminance
    'R', 'G', 'B',          # RGB
    'A', 'a',               # alpha (little-a for premultiplied)
    'C', 'M', 'Y', 'K',     # CMYK
)

class HistogramField(models.CharField):
    """
    Model field representing an image histogram.
    """
    
    def __init__(self, channel="L", *args, **kwargs):
        for arg in ('primary_key', 'unique'):
            if arg in kwargs:
                raise TypeError("'%s' is not a valid argument for %s." % (arg, self.__class__))
        if channel not in VALID_CHANNELS:
            raise TypeError("Invalid channel type %s was specified for HistogramField" % channel)
        self.channel = self.original_channel = channel
        kwargs['max_length'] = 1
        kwargs.setdefault('default', "L")
        kwargs.setdefault('verbose_name', "Histogram")
        kwargs.setdefault('max_length', 1)
        kwargs.setdefault('editable', True)
        kwargs.setdefault('blank', False)
        kwargs.setdefault('null', False)
        super(HistogramField, self).__init__(*args, **kwargs)
    
    def get_internal_type(self):
        return "CharField"
    
    def get_prep_lookup(self, lookup_type, value):
        return super(HistogramField, self).get_prep_lookup(self.original_channel)
    
    def get_prep_value(self, value):
        return unicode(self.original_channel)
    
    def contribute_to_class(self, cls, name):
        if not hasattr(self, 'db_column'):
            self.db_column = name
        if not hasattr(self, 'verbose_name'):
            self.verbose_name = name
        super(HistogramField, self).contribute_to_class(cls, name)
        
        #setattr(cls, self.channel, HistogramDescriptor(self))
        setattr(cls, 'channel', HistogramDescriptor(self))
        signals.pre_save.connect(self.refresh_histogram, sender=cls)
        
        if hasattr(self, 'original_channel'):
            for i in xrange(256):
                histocol = HistogramColumn(channel=self.original_channel)
                histocolname = "__%s_%02X" % (self.original_channel, i)
                histocol.db_column = histocolname
                histocol.verbose_name = histocolname
                self.creation_counter = histocol.creation_counter + 1
                cls.add_to_class(histocolname, histocol)
    
    def refresh_histogram(self, **kwargs):
        """
        Stores histogram column values in their respective db fields before saving
        """
        instance = kwargs.get('instance')
        pilimage = instance.image.pilimage
        
        logg.info("About to refresh '%s' histogram. KWARGS: %s" % (self.original_channel, kwargs))
        
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
        return ('django.db.models.CharField', args, kwargs)


