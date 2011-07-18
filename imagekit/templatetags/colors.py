import os
from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
from imagekit import colors

register = template.Library()

@register.filter()
def saturate(value, adjuster=u"0.1"):
    return u"#%s" % colors.Color(value).saturate(step=float(adjuster)).hex

@register.filter()
def desaturate(value, adjuster=u"0.1"):
    return u"#%s" %  colors.Color(value).desaturate(step=float(adjuster)).hex

@register.filter()
def darken(value, adjuster=u"0.1"):
    return u"#%s" %  colors.Color(value).darken(step=float(adjuster)).hex

@register.filter()
def lighten(value, adjuster=u"0.1"):
    return u"#%s" %  colors.Color(value).lighten(step=float(adjuster)).hex

@register.filter()
def inverse(value):
    return u"#%s" %  colors.Color(value).inverse.hex.upper()

@register.filter()
def analog(value):
    #return u"#%s" %  colors.Color(value).analog().hex.upper()
    return u"#%s" %  colors.Color(value).rotate_ryb(angle=20)

@register.filter()
def washout(value):
    return u"#%s" %  colors.Color(value).adjust_hsb(s=0.01, b=0.99, a=0.2).hex

@register.filter()
@stringfilter
def colorname(value):
    if hasattr(value, "complement"):
        return colors.guess_name(value)
    else:
        return colors.guess_name(colors.Color(value))

@register.filter()
def imagefilename(value):
    if hasattr(value, 'name'):
        return os.path.basename(value.name)
    elif hasattr(value._imgfield, 'name'):
        return os.path.basename(value._imgfield.name)
    return value
