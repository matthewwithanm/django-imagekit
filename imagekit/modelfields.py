import base64
from django.db import models
from django.db.models import fields
from django.db.models.fields import files
from django.db.models import signals
from ICCProfile import ICCProfile


class ICCDataField(models.TextField):
    """
    Model field representing an ICC profile instance.
    
    Represented in python as an ICCProfile instance -- see ICCProfile.py for details.
    Stored in the database as base64-encoded binary data.
    
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
            return ICCProfile(value)
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
        return ''
    
    def get_db_prep_value(self, value, connection, prepared=False):
        """
        Always return a valid base64-encoded string for valid data.
        """
        if not prepared:
            value = self.get_prep_value(value)
        if value:
            return value
        return ''
    
    def value_to_string(self, obj):
        """
        Return base64-encoded data (for now) suitable for serialization (JSON, pickle, etc)
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

