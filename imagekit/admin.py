
import os, numpy
from django.core import urlresolvers
from django.contrib import admin

from imagekit.lib import IK_ROOT
from imagekit.utils.ui import icon, arrow
from imagekit.utils import json, oldcolors, seriescolors
from imagekit.utils import ADict, AODict, xy, static
from imagekit.utils import logg
from imagekit.etc.profileinfo import profileinfo
from imagekit.etc.cieXYZ import cieYxy3
import imagekit.models

class ICCModelAdmin(admin.ModelAdmin):
    
    class Media:
        css = {'all': (
            static('css/iccprofile-admin.css'),
        )}
        js = (
            'https://ajax.googleapis.com/ajax/libs/jquery/1.5.2/jquery.min.js',
            'https://ajax.googleapis.com/ajax/libs/jqueryui/1.8.13/jquery-ui.min.js',
            static('flot/jquery.flot.js'),
            static('flot/jquery.flot.image.js'),
        )
    
    list_display = (
        'icc_download',
        #'modifydate',
        #'icc_description',
        'icc_colorspace',
        'icc_flot_cie1931',
        'icc_profileinfo_dump',
        'icc_flot_rgb_trc',
        #'icc_connectionspace',
        #'icc_renderingintent',
        #'icc_profileclass',
        #'icc_technology',
        #'icc_devicemodel',
        #'icc_manufacturer',
    )
    
    list_display_links = ('icc_colorspace',)
    list_per_page = 10
    
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
    
    def icc_profileinfo_dump(self, obj):
        if obj.icc:
            out = u"""
                <div class="profileinfo" id="profileinfo-%s">
                    <h3 class="profileinfo">
                        <a href="#">Details for &#8220;%s&#8221;</a>
                    </h3>
                    <div class="profileinfo-details">
                        <code>
                            <pre>
                                %s
                            </pre>
                        </code>
                    </div>
                </div>
                <script type="text/javascript">
                    $(document).ready(function() {
                        $("#profileinfo-%s").accordion({
                            active: false,
                            autoHeight: false,
                            animated: false,
                            collapsible: true
                        });
                    });
                </script>
            """ % (
                obj.icchash,
                obj.icc.getDescription(),
                profileinfo(obj.icc, barf=False),
                obj.icchash,
            )
            
            return out or u'<i style="color: lightgray;">No Info</i>'
        return u'<i style="color: lightgray;">None</i>'
    icc_profileinfo_dump.short_description = "Profile Details"
    icc_profileinfo_dump.allow_tags = True
    
    '''
    Flot graphs
    '''
    def icc_flot_cie1931(self, obj):
        if obj.icc:
            icc = obj.icc
            transformer = icc.transformer
            graphs = AODict()
            graphs.update({ 'bg':       ADict(series=[]), })
            graphs.update({ 'horshu':   ADict(series=[]), })
            
            # flot config options
            options = {
                'series': {
                    'points':           dict(show=True, fill=True, radius=3),
                    'lines':            dict(show=True, fill=False, lineWidth=1),
                    'images':           dict(show=True),
                },
                'xaxis':                dict(show=True, ticks=4, min=-0.1, max=0.85),
                'yaxis':                dict(show=True, ticks=4, min=-0.1, max=0.85),
                'grid':                 dict(show=False),
            }
            
            # gray line
            grayline = {
                'data':                 map(lambda iii: (1.025 - (float(iii) / 255.0), 0.025 + (float(iii) / 255.0)), xrange(0, 255, 5)),
                'lines':                dict(show=True, fill=False, lineWidth=1),
                'points':               dict(show=False),
                'images':               dict(show=False),
                'color':                '#eac',
                #'shadowSize':           0,
            }
            
            graphs.horshu.series.append(grayline)
            
            fullreversal = transformer.getRGBTristimulusXYZMatrix().I
            compander = transformer.getRGBTristimulusCompander()
            
            XYZ_wtpt = numpy.array(icc.tags.wtpt.values()).astype('float64')
            
            RGB_wtpt = numpy.asarray(
                numpy.dot(fullreversal, XYZ_wtpt).squeeze()
            )
            
            logg.info("XYZ_wtpt: %s" % XYZ_wtpt)
            logg.info("RGB_wtpt: %s" % RGB_wtpt)
            
            rgb_wtpt = compander(arg=RGB_wtpt)
            logg.info("rgb_wtpt: %s" % rgb_wtpt)
            
            rgb_wtpt_hex = compander(arg=RGB_wtpt, as_hex=True)
            logg.info("rgb_wtpt_hex: %s" % rgb_wtpt_hex)
            
            # tristimulii
            if 'rXYZ' in icc.tags.keys():
                graphs.horshu.series.append({ 'color': "#FC1919", 'data': [xy(icc.tags.rXYZ)], 'images': dict(show=False), })
            if 'gXYZ' in icc.tags.keys():
                graphs.horshu.series.append({ 'color': "#19FA19", 'data': [xy(icc.tags.gXYZ)], 'images': dict(show=False), })
            if 'bXYZ' in icc.tags.keys():
                graphs.horshu.series.append({ 'color': "#1991FF", 'data': [xy(icc.tags.bXYZ)], 'images': dict(show=False), })
            if 'wtpt' in icc.tags.keys():
                graphs.horshu.series.append({ 'color': rgb_wtpt_hex, 'data': [xy(icc.tags.wtpt)], 'images': dict(show=False), })
            
            # CIE'31 horseshoe curve
            graphs.horshu.series.append({ 'color': '#EFEFEF', 'data': cieYxy3, 'points': dict(show=False, fill=False), 'images': dict(show=False), })
            graphs.horshu.series.append({ 'color': '#EFEFEF', 'data': [cieYxy3[-1], cieYxy3[0]], 'points': dict(show=False, fill=False), 'images': dict(show=False), })
            
            out = graphs.horshu.series
            
            return u"""
                <span class="icc-cie1931" id="icc-cie1931-%s">
                    <div class="cie1931" id="cie1931-%s" style="width: %spx; height: %spx;"></div>
                </span>
                <script type="text/javascript">
                    $(document).ready(function () {
                        
                        var ciexyzbg = new Image(); ciexyzbg.src = '%s';
                        var series = %s;
                        var options = %s;
                        var plt;
                        
                        var img_data = [ [ [ "%s", 0, 0, 0.9, 0.9 ] ] ];
                        var img_options = {
                            series: { images: { show: true, alpha: 0.75 }, alpha: 0.75 },
                            xaxis: { min: -0.1, max: 0.85 },
                            yaxis: { min: -0.1, max: 0.85 },
                        };
                        
                        $.plot.image.loadDataImages(img_data, options, function () {
                            plt = $.plot(
                                $('#cie1931-%s'), img_data.concat(series), options
                            );
                        });
                        
                    });
                </script>
            """ % (
                obj.icchash,
                obj.icchash,
                361, 361,
                static('images/ciexyz.png'),
                json.dumps(out),
                json.dumps(options),
                static('images/ciexyz.png'),
                obj.icchash,
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
        theothers = imagekit.models.ICCModel.objects.filter(icchash__iexact=maybe.icchash)
        
        if theothers.count():
            self.message_user(request, "YO DOGG: that ICC file's signature was already in the database.")
            return theothers.all()[0]
        
        return maybe


class RGBHistogramAdmin(admin.ModelAdmin):
    
    class Media:
        css = { 'all': (
            static('css/iccprofile-admin.css'),
        )}
        js = (
            'https://ajax.googleapis.com/ajax/libs/jquery/1.5.2/jquery.min.js',
            static('flot/jquery.flot.js'),
            static('flot/jquery.flot.stack.js'),
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
    
    def rgb_flot_histogram(self, obj):
        series = []
        markings = []
        
        for k in obj.keys():
            #mean = float(obj[k].mean())
            #std = float(obj[k].std())
            mean = float(getattr(obj, k).mean())
            
            series.append({
                'color': seriescolors[k],
                'fillColor': seriescolors[k],
                'data': [list(s) for s in zip(
                    xrange(1, len(getattr(obj, k))+1),
                    getattr(obj, k).astype(float).tolist(),
                )],
                'clickable': True,
                'hoverable': True,
            })
            markings.append({
                'color': oldcolors[k],
                'lineWidth': 1,
                'yaxis': { 'from': mean, 'to': mean, },
            })
        
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
            static('css/iccprofile-admin.css'),
        )}
        js = (
            'https://ajax.googleapis.com/ajax/libs/jquery/1.5.2/jquery.min.js',
            static('flot/jquery.flot.js'),
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


class ProofAdmin(admin.ModelAdmin):

    class Media:
        css = { 'all': (
            static('css/iccprofile-admin.css'),
        )}
        js = (
            'https://ajax.googleapis.com/ajax/libs/jquery/1.5.2/jquery.min.js',
        )
    
    list_display = (
        'id',
        'with_sourceimage',
        'with_sourceprofile',
        'with_proofprofile',
        'intent',
        'proofintent',
    )
    
    list_display_links = ('id',)
    list_per_page = 10
    
    def with_sourceimage(self, obj):
        if obj.sourceprofile_id:
            return u"""
                <a href="%s">%s.%s (id: %s) %s</a>
            """ % (
                urlresolvers.reverse('admin:%s_%s_change' % (obj.content_type.app_label, obj.content_type.model), args=(obj.object_id,)),
                obj.content_type.app_label,
                obj.content_type.model_class().__name__,
                obj.object_id,
                arrow,
            )
        return u'<i style="color: gray;">No Source Image</i>'
    with_sourceimage.short_description = "Source Image"
    with_sourceimage.allow_tags = True
    
    def with_sourceprofile(self, obj):
        if obj.sourceprofile_id:
            return u"""
                <a href="%s">%s %s</a>
            """ % (
                urlresolvers.reverse('admin:imagekit_iccmodel_change', args=(obj.sourceprofile_id,)),
                obj.sourceprofile,
                arrow,
            )
        return u'<i style="color: gray;">No Source Profile</i>'
    with_sourceprofile.short_description = "Source ICC Profile"
    with_sourceprofile.allow_tags = True
    
    def with_proofprofile(self, obj):
        if obj.proofprofile_id:
            return u"""
                <a href="%s">%s %s</a>
            """ % (
                urlresolvers.reverse('admin:imagekit_iccmodel_change', args=(obj.proofprofile_id,)),
                obj.proofprofile,
                arrow,
            )
        return u'<i style="color: gray;">No Proof Profile</i>'
    with_proofprofile.short_description = "Proofing ICC Profile"
    with_proofprofile.allow_tags = True



admin.site.register(imagekit.models.ICCModel, ICCModelAdmin)
admin.site.register(imagekit.models.RGBHistogram, RGBHistogramAdmin)
admin.site.register(imagekit.models.LumaHistogram, LumaHistogramAdmin)
admin.site.register(imagekit.models.EnqueuedSignal)
admin.site.register(imagekit.models.Proof, ProofAdmin)

#admin.site.index_template = os.path.join(IK_ROOT, 'templates/admin/index_with_queues.html')
#admin.site.app_index_template = os.path.join(IK_ROOT, 'templates/admin/app_index.html')


