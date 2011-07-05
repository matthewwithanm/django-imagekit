import os, numpy
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from imagekit.utils import oldcolors, seriescolors, logg

register = template.Library()

@register.simple_tag
def version():
    import version
    return version.get_version()


@register.inclusion_tag('histogram.uint8.html', takes_context=True)
def histogram_channel(context, instance=None, histogram_channel='B'):
    
    logg.info("HISTOGRAM")
    
    if instance is not None:
        
        hc = histogram_channel[:1].upper()
        ht = ''
        w = 1
        h = 1
        image_uuid = ''
        flot_series = []
        markings = []
        
        if hc == 'L':
            histogram_mtx = instance.histogram_luma[hc]
            ht = 'luma'
            obj = instance.histogram_luma
        
        elif hc in 'RGB':
            histogram_mtx = instance.histogram_rgb[hc]
            ht = 'rgb'
            obj = instance.histogram_rgb
        
        if hasattr(instance, 'uuid'):
            image_uuid = instance.uuid
        else:
            import uuid
            image_uuid = uuid.uuid4().hex
        
        for k in obj.keys():
            mean = float(obj[k].mean())
            flot_series.append({
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
        
        # flot config options
        flot_options = {
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
        
        return dict(
            width=600,
            height=200,
            image_uuid=image_uuid,
            type=ht,
            flot_series=flot_series,
            flot_options=flot_options,
        )
    
    else:
        return
    
    
    
histogram_channel.is_safe = False

