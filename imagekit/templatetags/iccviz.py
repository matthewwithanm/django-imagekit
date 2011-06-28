import os, numpy
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from imagekit.etc.profileinfo import profileinfo
from imagekit.utils import json, xy, static
from imagekit.utils import ADict, AODict
from imagekit.utils import logg
from imagekit.utils.memoize import memoize
from imagekit.etc.cieXYZ import cieYxy3

register = template.Library()


class CIE31Options(AODict):
    """
    To draw the CIE-XYZ 1931 gamut, update those tristimulus struct(s) you wish to graph. Each must contain
    a data series with one single two-tuple -- the CIE-XYZ tristimulus converted to Yxy coordinates.
    
    """
    cie1931_bg_url =            static('images/ciexyz.png')
    width =                     361
    height =                    361
    
    flot_options = {            # CIE'31 Flot Defaults
        'series': {
            'points':           dict(show=True, fill=True, radius=3),
            'lines':            dict(show=True, fill=False, lineWidth=1),
            'images':           dict(show=True),
        },
        'xaxis':                dict(show=True, ticks=4, min=-0.1, max=0.85),
        'yaxis':                dict(show=True, ticks=4, min=-0.1, max=0.85),
        'grid':                 dict(show=False),
    }
    
    cie1931_graph = [           # SERIES: CIE-XYZ gamut graph outline. Data (two structs) is static
    { 'data':
        cieYxy3,                'color': '#EFEFEF',
                                'points': dict(show=False, fill=False),
                                'images': dict(show=False), },
    { 'data':
        [cieYxy3[-1],
        cieYxy3[0]],            'color': '#EFEFEF',
                                'points': dict(show=False, fill=False),
                                'images': dict(show=False), },
    ]
    
    grayline = {                # SERIES: gray diagonal line. Data is static.
        'color':                '#eac',
        'data':                 map(lambda iii: (1.025 - (float(iii) / 255.0), 0.025 + (float(iii) / 255.0)), xrange(0, 255, 5)),
        'lines':                dict(show=True, fill=False, lineWidth=1),
        'points':               dict(show=False),
        'images':               dict(show=False),
        'shadowSize':           0,
    }
    
    def __init__(self, *args, **kwargs):
        super(CIE31Options, self).__init__(*args, **kwargs)
        
        self.tristims = {       # Add one xy value as 'data' to each tristimulus.
            'rXYZ':             dict(color="#FC1919", images=dict(show=False)),
            'gXYZ':             dict(color="#19FA19", images=dict(show=False)),
            'bXYZ':             dict(color="#1991FF", images=dict(show=False)),
            'wtpt':             dict(color="#EFEFEF", images=dict(show=False)),
        }



class ToneCurveOptions(AODict):
    """
    To draw a tone-response curve, update the xTRC struct corresponding to the curves' channel
    with your algorithmic or interpolated data. The curve data table is typically generated for
    you by an ICC Profile's derived ICCTransformer instance, but profile LUTs and other tables
    can be graphed in the same way. To repurpose a struct for a field not represented here,
    change the 'color' attribute, as well as any other cosmetic properties as you need.

    """
    
    '''
    markings.append({
        'color': seriescolors[k],
        'yaxis': { 'from': (mean - std), 'to': (mean + std), },
    })
    '''
    
    graphs = AODict()
    graphs.update({ 'red':      ADict(series=[]), })
    graphs.update({ 'green':    ADict(series=[]), })
    graphs.update({ 'blue':     ADict(series=[]), })
    graphs.update({ 'luma':     ADict(series=[]), })
    
    container_width =           375
    width =                     120
    height =                    120
    
    flot_options = {       # Flot defaults for drawing profile tone response curves.
        'series': {
            'points':           dict(show=False, fill=True, radius=2),
            'lines':            dict(show=True, fill=True, lineWidth=1),
        },
        'xaxis':                dict(show=True, ticks=4, min=0, max=255),
        'yaxis':                dict(show=True, ticks=4, min=0.0, max=1.0),
        'grid':                 dict(show=False),
    }
    
    def __init__(self, *args, **kwargs):
        super(ToneCurveOptions, self).__init__(*args, **kwargs)
        
        self.tritones = {
            'rTRC':             dict(color="#FC1919", clickable=True, hoverable=True),
            'gTRC':             dict(color="#19FA19", clickable=True, hoverable=True),
            'bTRC':             dict(color="#1991FF", clickable=True, hoverable=True),
            'kTRC':             dict(color="#666666", clickable=True, hoverable=True),
        }



class ProfileInfoDisplayOptions(AODict):
    """
    This widget doesn't use Flot, so configuration is minimal -- a single jQuery UI call
    takes care of things; CSS handles dimensions and appearance. Pardon the stub.
    
    """
    
    def __init__(self, *args, **kwargs):
        super(ProfileInfoDisplayOptions, self).__init__(*args, **kwargs)



@register.inclusion_tag('profileinfo.html')
def profileinfo(icc=None):
    
    if icc:
        return dict(
            icc_profile_description=icc.getDescription(),
            icc_profile_hash=icc.getIDString(),
            icc_profile_info=profileinfo(icc, barf=False),
        )
    return dict()

profileinfo.is_safe = True


@register.inclusion_tag('tonecurve.html')
def tonecurve(icc=None, channel=None):
    
    if icc and channel:
        options = ToneCurveOptions()
        transformer = icc.transformer
        trilin = transformer.getRGBTristimulusLinearizer()
        
        curvedefinition = trilin['f%s' % channel.lower()]
        curvestruct = options.tritones['%sTRC' % channel.lower()]
        curvedata = [[i, curvedefinition(i).item()] for i in xrange(256)]
        curvestruct.update(dict(data=curvedata))
        
        return dict(
            container_width=options.container_width,
            width=options.width,
            height=options.height,
            channel=channel.lower()
            icc_profile_hash=icc.getIDString(),
            
            flot_options=json.dumps(options.flot_options),
            flot_series=json.dumps(curvedata),
        )
    return dict()

tonecurve.is_safe = True


@register.inclusion_tag('cie1931.html')
def cie1931(icc=None):
    
    if icc:
        options = CIE31Options()
        series = []
        
        for tag, struct in options.tristims.items():
            if tag in icc.tags.keys():
                tristim = [xy(icc.tags[tag])]
                struct.append(dict(data=tristim))
                series.append(struct)
        
        # special-case circa-1931 doodads.
        series.append(options.grayline)
        series.append(options.cie1931_graph)
        
        return dict(
            width=options.width,
            height=options.height,
            cie1931_bg_url=options.cie1931_bg_url,
            icc_profile_hash=icc.getIDString(),
            
            flot_options=json.dumps(options.flot_options),
            flot_series=json.dumps(series),
        )
    return dict()
    
cie1931.is_safe = True



