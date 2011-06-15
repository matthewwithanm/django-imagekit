import os
from django.conf import settings
from django.contrib import admin
from imagekit.models import ICCModel, RGBHistogram, LumaHistogram
from imagekit.ICCProfile import ADict, AODict
from imagekit.etc.cieXYZ import cieYxy3
from jogging import logging as logg
from memoize import memoize

try:
    import ujson as json
except ImportError:
    logg.info("--- Loading yajl in leu of ujson")
    try:
        import yajl as json
    except ImportError:
        logg.info("--- Loading simplejson in leu of yajl")
        try:
            import simplejson as json
        except ImportError:
            logg.info("--- Loading stdlib json module in leu of simplejson")
            import json

# The icon immediately below is copyright (C) 2011 Yusuke Kamiyamane -- All of his rights are reserved.
# It's licensed under Creative Commons Attribution 3.0: http://creativecommons.org/licenses/by/3.0/
# It comes from Mr. Kamiyamane's Fugue Icon Set: https://github.com/yusukekamiyamane/fugue-icons
icon = u"""
<img width="16" height="16" title="Download ICC File" alt="Download ICC File" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAgdJREFUeNqEk79r20AUx786R6dKxUUNNWmyeuxQCsZkaYd0DvkHOiRbpgydDfbgpUO0GUqzpYXMxf0HMrRTPHpKPSamoDrBgtrWyVLeO/2wAgUfHLovp/e993n3zmi320iSBPkwDGOfPttYP8adTqe/kQUhiqJ8Y6fb7X5eF91qtY75WxhUKhXM53Mt4zjGdf8QVcfUP2/tfcHvox+omo7WL8/eQyllFAY8hBCQUiIIAmO5XMKWAjXX0nucnS0kaparNe8vFovCYJ9qoJk5C8uy3g4GA9yPHdxMpQ5I1ACxNcEL9Sw9rGxA7v9n3t19JC+VQvj6FbIgxk0NmIWZ+9eHcKop894WMx8Rs5kxn+Hi4h7n5/+09rynKwNOhZmkLeDWysxUA8sqmOOY8WqZDjCbzR4bqIhSpDS1QRIhorXKNDMrFVK/qMKQDIQ24FT4xHebPSBMeSkUm71eLjXzwYGgskyzZtuA7/srA3Y8ufwD06nqHz69kfj58S8cM9VNYvY87/twOPyVF5Xq5msDZmEDIW1YbsqolA8pbLglZsdxriaTybfSxdxpPGbRNVARVKj0ZCTWXBOevE+9EjQajVuKyedMZ8As3MqnTW7TaWZuonlqFrrMXK/XMRqNVo/Pdd0P1MY76x4PMY8pk6+8DsOQO1G/Yr7LJzSfs9kaj7s87XywwYMAAwASbxzfXa6dmwAAAABJRU5ErkJggg==" />
"""

xy = lambda n: (n.X / (n.X + n.Y + n.Z), n.Y / (n.X + n.Y + n.Z))

class ICCModelAdmin(admin.ModelAdmin):
    
    class Media:
        css = { 'all': (
            os.path.join(settings.STATIC_URL, 'css/iccprofile-admin.css'),
        )}
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
                'grid': dict(show=False),
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
                series.append({ 'color': "#FC1919", 'data': [xy(icc.tags.rXYZ)], 'clickable': True, 'hoverable': True })
            if 'gXYZ' in icc.tags.keys():
                series.append({ 'color': "#19FA19", 'data': [xy(icc.tags.gXYZ)], 'clickable': True, 'hoverable': True })
            if 'bXYZ' in icc.tags.keys():
                series.append({ 'color': "#1991FF", 'data': [xy(icc.tags.bXYZ)], 'clickable': True, 'hoverable': True })
            if 'wtpt' in icc.tags.keys():
                series.append({ 'color': "#000000", 'data': [xy(icc.tags.wtpt)], 'clickable': True, 'hoverable': True })
            
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
            transformer = icc.transformer
            graphs = AODict()
            graphs.update({ 'red':      ADict(series=[]), })
            graphs.update({ 'green':    ADict(series=[]), })
            graphs.update({ 'blue':     ADict(series=[]), })
            graphs.update({ 'luma':     ADict(series=[]), })
            
            if not transformer:
                return u'<i style="color: lightgray;">No Transformer</i>' 
            
            # flot config options
            options = {
                'series': {
                    'points': dict(show=False, fill=True, radius=2),
                    'lines': dict(show=True, fill=True, lineWidth=1),
                },
                'xaxis': dict(show=True, ticks=4, min=0, max=255),
                'yaxis': dict(show=True, ticks=4, min=0.0, max=1.0),
                'grid': dict(show=False),
            }
            
            trilin = transformer.getRGBTristimulusLinearizer()
            
            if 'rTRC' in icc.tags.keys():
                graphs.red.series.append({ 'color': "#FC1919", 'data': [[i, trilin.fr(i).item()] for i in xrange(256)], 'clickable': True, 'hoverable': True })
            if 'gTRC' in icc.tags.keys():
                graphs.green.series.append({ 'color': "#19FA19", 'data': [[i, trilin.fg(i).item()] for i in xrange(256)], 'clickable': True, 'hoverable': True })
            if 'bTRC' in icc.tags.keys():
                graphs.blue.series.append({ 'color': "#1991FF", 'data': [[i, trilin.fb(i).item()] for i in xrange(256)], 'clickable': True, 'hoverable': True })
            
            
            outopts = json.dumps(options)
            out = u"""
                <div class="icc-rgb-trc" style="width: 375px;">
            """
            
            for channel, bitstream in graphs.items():
                if len(bitstream['series']) > 0:
                    out += """
                        <div class="rgb-trc" id="rgb-trc-%s-%s" style="width: %spx; height: %spx;"></div>
                        <script type="text/javascript">
                            $(document).ready(function () {
                                $.plot(
                                    $('#rgb-trc-%s-%s'),
                                    %s,
                                    %s
                                );
                            });
                        </script>
                    """ % (
                        obj.icchash, channel,
                        120, 120,
                        obj.icchash, channel,
                        json.dumps(bitstream['series']),
                        outopts,
                    )
            
            out += u"""
                </div>
            """
            
            
            return out
        
        # no-icc default
        return u'<i style="color: lightgray;">None</i>'
    icc_flot_rgb_trc.short_description = "Tone Response Curves"
    icc_flot_rgb_trc.allow_tags = True
    
    
    '''
    ModelAdmin overrides
    '''
    
    def save_form(self, request, form, change):
        maybe = super(ICCModelAdmin, self).save_form(request, form, change)
        theothers = ICCModel.objects.filter(icchash__iexact=maybe.icchash)
        
        if theothers.count():
            self.message_user(request, "YO DOGG: that ICC file's signature was already in the database.")
            return theothers.all()[0]
        
        return maybe


class SeriesColors(ADict):
    def __init__(self):
        self.R = "#FF1919"
        self.G = "#19FA19"
        self.B = "#1991FF"
        self.L = "#CCCCCC"

class SeriesColorsAlpha(ADict):
    def __init__(self):
        self.R = "rgba(165, 5, 15, 0.65)"
        self.G = "rgba(10, 175, 85, 0.75)"
        self.B = "rgba(12, 13, 180, 0.15)"
        self.L = "rgba(221, 221, 221, 0.45)"

oldcolors = SeriesColors()
seriescolors = SeriesColorsAlpha()

class RGBHistogramAdmin(admin.ModelAdmin):
    
    class Media:
        css = { 'all': (
            os.path.join(settings.STATIC_URL, 'css/iccprofile-admin.css'),
        )}
        js = (
            'https://ajax.googleapis.com/ajax/libs/jquery/1.5.2/jquery.min.js',
            os.path.join(settings.STATIC_URL, 'flot/jquery.flot.js'),
            os.path.join(settings.STATIC_URL, 'flot/jquery.flot.stack.js'),
        )
    
    list_display = (
        'id',
        'rgb_flot_histogram',
        'object_id',
        'content_type',
        'imagewithmetadata',
    )
    
    list_display_links = ('id',)
    list_per_page = 5
    
    @memoize
    def rgb_flot_histogram(self, obj):
        series = []
        markings = []
        
        for k in obj.keys():
            mean = float(obj[k].mean())
            #std = float(obj[k].std())
            series.append({
                'color': seriescolors[k],
                'fillColor': seriescolors[k],
                'data': [list(s) for s in zip(
                    xrange(1, len(obj[k])+1),
                    obj[k].astype(float).tolist(),
                )],
                'clickable': True,
                'hoverable': True,
            })
            markings.append({
                'color': oldcolors[k],
                'lineWidth': 1,
                'yaxis': { 'from': mean, 'to': mean, },
            })
            '''
            markings.append({
                'color': seriescolors[k],
                'yaxis': { 'from': (mean - std), 'to': (mean + std), },
            })
            '''
        
        # flot config options
        options = {
            'series': {
                #'stack': True,
                'points': dict(show=False, fill=True, radius=2),
                'lines': dict(show=False, fill=True, lineWidth=1),
                'bars': dict(show=True, fill=True, barWidth=1, lineWidth=0),
            },
            'xaxis': dict(show=True, ticks=12),
            'yaxis': dict(show=True, ticks=4, min=0.0),
            'grid': dict(show=True, markings=markings, autoHighlight=True, borderWidth=1, color="#CCCCCC", borderColor="#BABABA"),
        }
        
        return u"""
            <span class="histogram-rgb">
                <div class="rgb" id="rgb-%s" style="width: %spx; height: %spx;"></div>
            </span>
            <script type="text/javascript">
                $(document).ready(function () {
                    $.plot(
                        $('#rgb-%s'),
                        %s,
                        %s
                    );
                });
            </script>
        """ % (
            obj.pk,
            600, 250,
            obj.pk,
            json.dumps(series),
            json.dumps(options),
        )
    rgb_flot_histogram.short_description = "RGB Histograms"
    rgb_flot_histogram.allow_tags = True


class LumaHistogramAdmin(admin.ModelAdmin):

    class Media:
        css = { 'all': (
            os.path.join(settings.STATIC_URL, 'css/iccprofile-admin.css'),
        )}
        js = (
            'https://ajax.googleapis.com/ajax/libs/jquery/1.5.2/jquery.min.js',
            os.path.join(settings.STATIC_URL, 'flot/jquery.flot.js'),
        )
    
    list_display = (
        'id',
        'luma_flot_histogram',
        'object_id',
        'content_type',
        'imagewithmetadata',
    )
    
    list_display_links = ('id',)
    list_per_page = 10
    
    '''
    Flot graphs
    '''
    def luma_flot_histogram(self, obj):
        if obj.L.any():
            series = []
            
            # flot config options
            options = {
                'series': {
                    'points': dict(show=False, fill=True, radius=2),
                    'lines': dict(show=False, fill=True, lineWidth=1),
                    'bars': dict(show=True, fill=True, barWidth=1, fillColor="#ccc"),
                },
                'xaxis': dict(show=True, ticks=4),
                'yaxis': dict(show=True, ticks=4),
                'grid': dict(show=False),
            }
            
            series.append({
                'color': "#ccc",
                'data': [list(s) for s in zip(
                    xrange(1, len(obj.L)+1),
                    list(obj.L.astype(float)),
                )], 
                'clickable': True,
                'hoverable': True,
            })
            
            return u"""
                <span class="histogram-luma">
                    <div class="luma" id="luma-%s" style="width: %spx; height: %spx;"></div>
                </span>
                <script type="text/javascript">
                    $(document).ready(function () {
                        $.plot(
                            $('#luma-%s'),
                            %s,
                            %s
                        );
                    });
                </script>
            """ % (
                obj.pk,
                600, 250,
                obj.pk,
                json.dumps(series),
                json.dumps(options),
            )
        # no-icc default
        return u'<i style="color: lightgray;">None</i>'
    luma_flot_histogram.short_description = "Luma Histogram"
    luma_flot_histogram.allow_tags = True


admin.site.register(ICCModel, ICCModelAdmin)
admin.site.register(RGBHistogram, RGBHistogramAdmin)
admin.site.register(LumaHistogram, LumaHistogramAdmin)
