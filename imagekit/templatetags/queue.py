import os, numpy, socket
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from imagekit.signals import KewGardens
from imagekit.queue import queues

register = template.Library()

@register.simple_tag
def queue_length(queue_name):
    return KewGardens(queue_name=queue_name).queue_length()

@register.simple_tag
def queue_classname(queue_name):
    return str(queues[queue_name].__class__.__name__)

@register.simple_tag
def sock_status_url():
    return "ws://%s:%s/sock/status" % (socket.gethostname().lower(), settings.IK_QUEUE_SERVER_PORT)

@register.inclusion_tag('admin/sidebar_queue_module.html', takes_context=True)
def sidebar_queue_module(context):
    qs = dict(queues.items())
    default = qs.pop('default')
    return dict(default=default, queues=qs)



