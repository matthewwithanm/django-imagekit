from django.conf import settings
from imagekit.queue import backends

if not hasattr(settings, 'IK_QUEUES'):
    raise ImproperlyConfigured('The IK_QUEUES setting is required.')

if 'default' not in settings.IK_QUEUES:
    raise ImproperlyConfigured("The required default queue definition is missing from IK_QUEUES.")

queues = backends.ConnectionHandler(settings.IK_QUEUES)
queue = queues['default']


