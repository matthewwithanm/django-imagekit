import os, json
from django.conf import settings
from django.contrib import admin
from imagekit.models import ICCModel
from imagekit.etc.cieXYZ import cieYxy3

# The icon immediately below is copyright (C) 2011 Yusuke Kamiyamane -- All of his rights are reserved.
# It's licensed under Creative Commons Attribution 3.0: http://creativecommons.org/licenses/by/3.0/
# It comes from Mr. Kamiyamane's Fugue Icon Set: https://github.com/yusukekamiyamane/fugue-icons
icon = u"""
<img width="16" height="16" title="Download ICC File" alt="Download ICC File" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAgdJREFUeNqEk79r20AUx786R6dKxUUNNWmyeuxQCsZkaYd0DvkHOiRbpgydDfbgpUO0GUqzpYXMxf0HMrRTPHpKPSamoDrBgtrWyVLeO/2wAgUfHLovp/e993n3zmi320iSBPkwDGOfPttYP8adTqe/kQUhiqJ8Y6fb7X5eF91qtY75WxhUKhXM53Mt4zjGdf8QVcfUP2/tfcHvox+omo7WL8/eQyllFAY8hBCQUiIIAmO5XMKWAjXX0nucnS0kaparNe8vFovCYJ9qoJk5C8uy3g4GA9yPHdxMpQ5I1ACxNcEL9Sw9rGxA7v9n3t19JC+VQvj6FbIgxk0NmIWZ+9eHcKop894WMx8Rs5kxn+Hi4h7n5/+09rynKwNOhZmkLeDWysxUA8sqmOOY8WqZDjCbzR4bqIhSpDS1QRIhorXKNDMrFVK/qMKQDIQ24FT4xHebPSBMeSkUm71eLjXzwYGgskyzZtuA7/srA3Y8ufwD06nqHz69kfj58S8cM9VNYvY87/twOPyVF5Xq5msDZmEDIW1YbsqolA8pbLglZsdxriaTybfSxdxpPGbRNVARVKj0ZCTWXBOevE+9EjQajVuKyedMZ8As3MqnTW7TaWZuonlqFrrMXK/XMRqNVo/Pdd0P1MY76x4PMY8pk6+8DsOQO1G/Yr7LJzSfs9kaj7s87XywwYMAAwASbxzfXa6dmwAAAABJRU5ErkJggg==" />
"""

xy = lambda ill: (ill['X'] / (ill['X']+ill['Y']+ill['Z']), ill['Y'] / (ill['X']+ill['Y']+ill['Z']))

class ICCModelAdmin(admin.ModelAdmin):
    
    class Media:
        js = (
            'https://ajax.googleapis.com/ajax/libs/jquery/1.5.2/jquery.min.js',
            os.path.join(settings.STATIC_URL, 'flot/jquery.flot.js'),
        )
    
    list_display = (
        'icc_download',
        'modifydate',
        'icc_description',
        'icc_flot_cie1931',
        'icc_flot_rgb_trc',
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
    Flot graphs
    '''
    def icc_flot_cie1931(self, obj):
        if obj.icc:
            icc = obj.icc
            series = []
            
            # flot config options
            options = {
                'series': {
                    'points': dict(show=True, fill=True, radius=2),
                    'lines': dict(show=True, fill=False, lineWidth=1),
                },
                'xaxis': dict(show=True, ticks=4, min=-0.1, max=0.85),
                'yaxis': dict(show=True, ticks=4, min=-0.1, max=0.85),
                'grid': dict(show=True),
            }

            # gray line
            series.append({
                'color': '#eac',
                'data': map(lambda iii: (1.025-(float(iii)/255.0), 0.025+(float(iii)/255.0)), xrange(0, 255, 5)),
                'points': dict(show=False, fill=False),
                'shadowSize': 0,
            })
            
            # tristimulii
            if 'rXYZ' in icc.tags.keys():
                series.append({ 'color': "#FC1919", 'data': [xy(icc.tags.get('rXYZ'))], 'clickable': True, 'hoverable': True })
            if 'gXYZ' in icc.tags.keys():
                series.append({ 'color': "#19FA19", 'data': [xy(icc.tags.get('gXYZ'))], 'clickable': True, 'hoverable': True })
            if 'bXYZ' in icc.tags.keys():
                series.append({ 'color': "#1991FF", 'data': [xy(icc.tags.get('bXYZ'))], 'clickable': True, 'hoverable': True })
            if 'wtpt' in icc.tags.keys():
                series.append({ 'color': "#000000", 'data': [xy(icc.tags.get('wtpt'))], 'clickable': True, 'hoverable': True })
            
            # CIE'31 horseshoe curve
            series.append({ 'color': '#EFEFEF', 'data': cieYxy3, 'points': dict(show=False, fill=False), })
            series.append({ 'color': '#EFEFEF', 'data': [cieYxy3[-1], cieYxy3[0]], 'points': dict(show=False, fill=False), })
            
            return u"""
                <span class="icc-cie1931">
                    <div class="cie1931" id="cie1931-%s" style="width: %spx; height: %spx;"></div>
                </span>
                <script type="text/javascript">
                    $(document).ready(function () {
                        $.plot(
                            $('#cie1931-%s'),
                            %s,
                            %s
                        );
                    });
                </script>
            """ % (
                obj.icchash,
                250, 250,
                obj.icchash,
                json.dumps(series),
                json.dumps(options),
            )
        
        # no-icc default
        return u'<i style="color: lightgray;">None</i>'
    icc_flot_cie1931.short_description = "CIE-XYZ 1931 Tristimulus Plot"
    icc_flot_cie1931.allow_tags = True
    
    def icc_flot_rgb_trc(self, obj):
        if obj.icc:
            icc = obj.icc
            series = []
            transformer = icc.transformer
            
            if not transformer:
                return u'<i style="color: lightgray;">No Transformer</i>' 
            
            # flot config options
            options = {
                'series': {
                    'points': dict(show=True, fill=True, radius=2),
                    'lines': dict(show=True, fill=False, lineWidth=1),
                },
                'xaxis': dict(show=True, ticks=4, min=0, max=255),
                'yaxis': dict(show=True, ticks=4, min=0.0, max=1.0),
                'grid': dict(show=True),
            }
            
            trilin = transformer.getRGBTristimulusLinearizer()
            
            if 'rTRC' in icc.tags.keys():
                series.append({ 'color': "#FC1919", 'data': [[i, trilin.fr(i).item()] for i in xrange(256)], 'clickable': True, 'hoverable': True })
            if 'gTRC' in icc.tags.keys():
                series.append({ 'color': "#19FA19", 'data': [[i, trilin.fg(i).item()] for i in xrange(256)], 'clickable': True, 'hoverable': True })
            if 'bTRC' in icc.tags.keys():
                series.append({ 'color': "#1991FF", 'data': [[i, trilin.fb(i).item()] for i in xrange(256)], 'clickable': True, 'hoverable': True })
            
            
            return u"""
                <span class="icc-rgb-trc">
                    <div class="rgb-trc" id="rgb-trc-%s" style="width: %spx; height: %spx;"></div>
                </span>
                <script type="text/javascript">
                    $(document).ready(function () {
                        $.plot(
                            $('#rgb-trc-%s'),
                            %s,
                            %s
                        );
                    });
                </script>
            """ % (
                obj.icchash,
                250, 250,
                obj.icchash,
                json.dumps(series),
                json.dumps(options),
            )
        
        # no-icc default
        return u'<i style="color: lightgray;">None</i>'
    icc_flot_rgb_trc.short_description = "Tone Response Curves"
    icc_flot_rgb_trc.allow_tags = True
    
    
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

admin.site.register(ICCModel, ICCModelAdmin)