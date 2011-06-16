import os, numpy
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def version():
    import version
    return version.get_version()


@register.inclusion_tag('histogram.uint8.html')
def histogram_uint8(histogram_channel=None):
    return dict(histogram_channel=histogram_channel)
histogram_uint8.is_safe = True

