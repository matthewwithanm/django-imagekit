#!/usr/bin/env python
# encoding: utf-8
"""
backends.py

Backend classes for the imagekit async queue.

Created by FI$H 2000 on 2011-06-29.
Copyright (c) 2011 OST, LLC. All rights reserved.

"""

from django.utils import importlib
from django.core.exceptions import ImproperlyConfigured
from imagekit.utils import AODict

class QueueBase(object):
    
    def __init__(self, *args, **kwargs):
        """
        It's a good idea to call super() first in your overrides,
        to take care of params and whatnot like these.
        
        """
        
        super(QueueBase, self).__init__()
        self.queue_name = kwargs.pop('queue_name', "imagekit_queue")
        self.queue_options = {}
        self.queue_options.update(kwargs.pop('queue_options', {}))
    
    def ping(self):
        raise NotImplementedError("WTF: Queue backend needs a Queue.ping() implementaton")
    
    def push(self, value):
        raise NotImplementedError("WTF: Queue backend needs a Queue.push() implementaton")
    
    def pop(self):
        raise NotImplementedError("WTF: Queue backend needs a Queue.pop() implementaton")
    
    def count(self):
        return -1
    
    def clear(self):
        raise NotImplementedError("WTF: Queue backend needs a Queue.flush() implementaton")
    
    def values(self):
        raise NotImplementedError("WTF: Queue backend needs a Queue.values() implementaton")
    
    def __unicode__(self):
        return u"<QueueBase name:%s count:%s options:%s>" % (self.queue_name, self.count(), self.queue_options)
    
    def next(self):
        if not self.count() > 0:
            raise StopIteration
        return self.pop()
    
    def __iter__(self):
        return self

class RedisQueue(QueueBase):
    
    def __init__(self, *args, **kwargs):
        """
        The RedisQueue is the default queue backend. The QueueBase methods are mapped to 
        a Redis list; the redis-py module is required:
        
            https://github.com/andymccurdy/redis-py
        
        Redis is simple and fast, out of the box. The hiredis C library and python wrappers
        can be dropped into your install, to make it faster:
        
            https://github.com/pietern/hiredis-py
        
        To configure Redis, we pass the queue OPTIONS dict off wholesale to the python
        redis constructor -- Simply stick any Redis kwarg options you need into the OPTIONS
        setting. All the redis options can be furthermore specified in the RedisQueue constructor
        as a queue_options dict to override settings.py.
        
        """
        super(RedisQueue, self).__init__(*args, **kwargs)
        
        try:
            import redis
        except ImportError:
            raise IOError("WTF: Can't import redis python module.")
        else:
            self.r = redis.Redis(**self.queue_options)
    
    def ping(self):
        return self.r.ping()
    
    def push(self, value):
        self.r.rpush(self.queue_name, value)
    
    def pop(self):
        return self.r.lpop(self.queue_name)
    
    def count(self):
        return self.r.llen(self.queue_name)
    
    def clear(self):
        self.r.delete(self.queue_name)
    
    def values(self, floor=0, ceil=-1):
        return self.r.lrange(self.queue_name, floor, ceil)

class DatabaseQueueProxy(QueueBase):
    """
    The DatabaseQueueProxy doesn't directly instantiate; instead, this proxy object
    will set up a model manager you specify in your settings as a queue backend.
    This allows you to use a standard database-backed model to run a queue.
    
    A working implementation of such a model manageris available in imagekit/models.py.
    To use it, sync the EnqueuedSignal model to your database and configure the queue like so:
    
        IK_QUEUES = {
            'default': {
                'NAME': 'imagekit_database_queue',
                'ENGINE': 'imagekit.queue.backends.DatabaseQueueProxy',
                'OPTIONS': dict(app_label='imagekit', modl_name='EnqueuedSignal'),
            },
        }
    
    This is useful for:
    
        * Debugging -- the queue can be easily inspected via the admin interface;
          dequeued objects aren't deleted by default (the 'enqueued' boolean field
          is set to False when instances are dequeued).
        * Less moving parts -- useful if you don't want to set up another service
          (e.g. Redis) to start working with queued signals.
        * Fallback functionality -- you can add logic to set up a database queue
          if the queue backend you want to use is somehow unavailable, to keep from
          losing signals e.g. while scaling Amazon AMIs or transitioning your
          servers to new hosts.
    
    """
    def __new__(cls, *args, **kwargs):
        
        if 'app_label' in kwargs['queue_options']:
            if 'modl_name' in kwargs['queue_options']:
                
                from django.db.models.loading import cache
                mgr = kwargs['queue_options'].get('manager', "objects")
                
                ModlCls = cache.get_model(app_label=kwargs['queue_options'].get('app_label'), model_name=kwargs['queue_options'].get('modl_name'))
                mgr_instance = getattr(ModlCls, mgr)
                mgr_instance.queue_name = kwargs.pop('queue_name', "imagekit_queue")
                mgr_instance.queue_options.update(kwargs.pop('queue_options', {}))
                
                return mgr_instance
            
            else:
                raise ImproperlyConfigured("DatabaseQueueProxy's queue configuration requires the name of the model class to use to be specified in in 'modl_name'.")
        
        else:
            raise ImproperlyConfigured("DatabaseQueueProxy's queue configuration requires you to specify 'app_label', an app in which your 'modl_name' is defined in models.py.")

"""
Class-loading functions.

ConnectionHandler, import_class() and load_backend() are based on original implementations
from the django-haystack app:

    https://github.com/toastdriven/django-haystack/blob/master/haystack/utils/loading.py
    https://github.com/toastdriven/django-haystack/

See the Haystack source for details.

"""
def import_class(path):
    path_bits = path.split('.') # Cut off the class name at the end.
    class_name = path_bits.pop()
    module_path = '.'.join(path_bits)
    module_itself = importlib.import_module(module_path)
    if not hasattr(module_itself, class_name):
        raise ImportError("The Python module '%s' has no '%s' class." % (module_path, class_name))
    return getattr(module_itself, class_name)

def load_backend(full_backend_path):
    path_bits = full_backend_path.split('.')
    if len(path_bits) < 2:
        raise ImproperlyConfigured("The provided backend '%s' is not a complete Python path to a QueueBase subclass." % full_backend_path)
    return import_class(full_backend_path)

class ConnectionHandler(object):
    def __init__(self, connections_info):
        self.connections_info = connections_info
        self._connections = {}
        self._index = None
    
    def ensure_defaults(self, alias):
        try:
            conn = self.connections_info[alias]
        except KeyError:
            raise ImproperlyConfigured("The key '%s' isn't an available connection." % alias)
        
        if not conn.get('ENGINE'):
            conn['ENGINE'] = 'imagekit.queue.backends.RedisQueue' # default to the Redis backend
    
    def __getitem__(self, key):
        if key in self._connections:
            return self._connections[key]
        
        self.ensure_defaults(key)
        
        ConnectionClass = load_backend(self.connections_info[key]['ENGINE'])
        self._connections[key] = ConnectionClass(
            queue_name=self.connections_info[key].get('NAME'),
            queue_options=self.connections_info[key].get('OPTIONS', {}),
        )
        return self._connections[key]
    
    def all(self):
        return [self[alias] for alias in self.connections_info]


