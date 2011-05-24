from django.contrib import admin
from imagekit.models import ICCModel

# The icon immediately below is copyright (C) 2011 Yusuke Kamiyamane -- All of his rights are reserved.
# It's licensed under Creative Commons Attribution 3.0: http://creativecommons.org/licenses/by/3.0/
# It comes from Mr. Kamiyamane's Fugue Icon Set: https://github.com/yusukekamiyamane/fugue-icons
icon = u"""
<img width="16" height="16" title="Download ICC File" alt="Download ICC File" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAgdJREFUeNqEk79r20AUx786R6dKxUUNNWmyeuxQCsZkaYd0DvkHOiRbpgydDfbgpUO0GUqzpYXMxf0HMrRTPHpKPSamoDrBgtrWyVLeO/2wAgUfHLovp/e993n3zmi320iSBPkwDGOfPttYP8adTqe/kQUhiqJ8Y6fb7X5eF91qtY75WxhUKhXM53Mt4zjGdf8QVcfUP2/tfcHvox+omo7WL8/eQyllFAY8hBCQUiIIAmO5XMKWAjXX0nucnS0kaparNe8vFovCYJ9qoJk5C8uy3g4GA9yPHdxMpQ5I1ACxNcEL9Sw9rGxA7v9n3t19JC+VQvj6FbIgxk0NmIWZ+9eHcKop894WMx8Rs5kxn+Hi4h7n5/+09rynKwNOhZmkLeDWysxUA8sqmOOY8WqZDjCbzR4bqIhSpDS1QRIhorXKNDMrFVK/qMKQDIQ24FT4xHebPSBMeSkUm71eLjXzwYGgskyzZtuA7/srA3Y8ufwD06nqHz69kfj58S8cM9VNYvY87/twOPyVF5Xq5msDZmEDIW1YbsqolA8pbLglZsdxriaTybfSxdxpPGbRNVARVKj0ZCTWXBOevE+9EjQajVuKyedMZ8As3MqnTW7TaWZuonlqFrrMXK/XMRqNVo/Pdd0P1MY76x4PMY8pk6+8DsOQO1G/Yr7LJzSfs9kaj7s87XywwYMAAwASbxzfXa6dmwAAAABJRU5ErkJggg==" />
"""

class ICCModelAdmin(admin.ModelAdmin):
    list_display = (
        'icc_download',
        'modifydate',
        'icc_description',
        'icc_colorspace',
        'icc_connectionspace',
        'icc_renderingintent',
        'icc_profileclass',
        'icc_technology',
        'icc_devicemodel',
        'icc_manufacturer',
    )
    
    list_display_links = ('modifydate',)
    
    '''
    List view accessors to display ICC profile object parameters in the Django admin.
    '''
    def icc_description(self, obj):
        if obj.icc:
            return obj.icc.getDescription() or u'<i style="color: lightgray;">None</i>'
        return u'<i style="color: lightgray;">None</i>'
    icc_description.short_description = "Description"
    icc_description.allow_tags = True
    
    def icc_download(self, obj):
        if obj.iccfile:
            if obj.iccfile.url:
                return '''
                    <a href="%s">%s</a>
                ''' % (obj.iccfile.url, icon)
            else:
                u'<i style="color: lightgray;">Unavailable</i>'
        return u'<i style="color: lightgray;">No File</i>'
    icc_download.short_description = "File D/L"
    icc_download.allow_tags = True
    
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
    
    def icc_renderingintent(self, obj):
        if obj.icc:
            return obj.icc.getRenderingIntent() or u'<i style="color: lightgray;">None</i>'
        return u'<i style="color: lightgray;">None</i>'
    icc_renderingintent.short_description = "Rendering Intent"
    icc_renderingintent.allow_tags = True
    
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
    
    '''
    ModelAdmin overrides
    '''
    
    """
    def save_model(self, request, obj, form, change):
        from django.db import IntegrityError
        
        try:
            obj.save()
        except IntegrityError:
            self.message_user(request, "YO DOGG: that ICC file's signature was already in the database.")
    """
    
    def save_form(self, request, form, change):
        maybe = super(ICCModelAdmin, self).save_form(request, form, change)
        theothers = ICCModel.objects.filter(icchash__iexact=maybe.icchash)
        
        if theothers.count():
            self.message_user(request, "YO DOGG: that ICC file's signature was already in the database.")
            return theothers.all()[0]
        
        return maybe
    
    
    
#admin.site.register(ICCModel, ICCModelAdmin)