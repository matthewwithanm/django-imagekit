from django.contrib import admin
from imagekit.models import ICCModel

class ICCModelAdmin(admin.ModelAdmin):
    list_display = (
        'modifydate',
        'icc_description',
        'icc_colorspace',
        'icc_connectionspace',
        'icc_profileclass',
        'icc_technology',
        'icc_devicemodel',
        'icc_manufacturer',
    )
    
    def icc_description(self, obj):
        if obj.icc:
            return obj.icc.getDescription() or u'<i style="color: lightgray;">None</i>'
        return u'<i style="color: lightgray;">None</i>'
    icc_description.short_description = "Description"
    icc_description.allow_tags = True
    
    def icc_manufacturer(self, obj):
        if obj.icc:
            return obj.icc.getDeviceManufacturerDescription() or u'<i style="color: lightgray;">None</i>'
        return u'<i style="color: lightgray;">None</i>'
    icc_manufacturer.short_description = "Manufacturer"
    icc_manufacturer.allow_tags = True
    
    def icc_devicemodel(self, obj):
        if obj.icc:
            return obj.icc.getDeviceModelDescription() or u'<i style="color: lightgray;">None</i>'
        return u'<i style="color: lightgray;">None</i>'
    icc_devicemodel.short_description = "Device Model"
    icc_devicemodel.allow_tags = True
    
    def icc_profileclass(self, obj):
        if obj.icc:
            return obj.icc.getProfileClass() or u'<i style="color: lightgray;">None</i>'
        return u'<i style="color: lightgray;">None</i>'
    icc_profileclass.short_description = "Profile Class"
    icc_profileclass.allow_tags = True
    
    def icc_technology(self, obj):
        if obj.icc:
            return obj.icc.getTechnologySummary() or u'<i style="color: lightgray;">None</i>'
        return u'<i style="color: lightgray;">None</i>'
    icc_technology.short_description = "Technology Summary"
    icc_technology.allow_tags = True
    
    def icc_colorspace(self, obj):
        if obj.icc:
            return unicode(obj.icc.colorSpace) or u'<i style="color: lightgray;">None</i>'
        return u'<i style="color: lightgray;">None</i>'
    icc_colorspace.short_description = "Colorspace"
    icc_colorspace.allow_tags = True
    
    def icc_connectionspace(self, obj):
        if obj.icc:
            return obj.icc.connectionColorSpace or u'<i style="color: lightgray;">None</i>'
        return u'<i style="color: lightgray;">None</i>'
    icc_connectionspace.short_description = "Connection space (PCS)"
    icc_connectionspace.allow_tags = True
    
    

#admin.site.register(ICCModel, ICCModelAdmin)