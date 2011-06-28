'''
ImageKit signal definitions.

'''

import hashlib, uuid, PIL
import django.dispatch
from django.conf import settings
import imagekit.json as json
import imagekit

class KewGardens(object):
    forkedpath = lambda s: "imagekit_%s" % s
    garden = None
    queuename = None
    queue_in = None
    queue_out = None
    
    id_map = {
        'instance': lambda i: (i.pk, obj._meta.app_label, obj.__class__.__name__.lower()),
        'iccdata': lambda iccdata: (hashlib.sha1(iccdata.data).hexdigest(), 'imagekit', 'iccmodel'),
    }
    
    id_remap = {
        'instance': lambda modlcls, pk: modlcls.objects.get(pk=pk),
        'iccdata': lambda modlcls, hsh: modlcls.objects.get(icchash__exact=hsh).icc,
    }
    
    def __init__(self, *args, **kwargs):
        runmode = kwargs.pop('runmode', None)
        self.signals = kwargs.pop('signals', {})
        super(KewGardens, self).__init__(*args, **kwargs)
        
        if not runmode:
            runmode = settings.IK_RUNMODE
        self.runmode = runmode
        
        if not self.runmode == imagekit.IK_SYNC:
            # not running with synchronous calls, we need a queue
            try:
                import redis
            except ImportError:
                raise IOError("Can't import redis-py to connect to queue")
            else:
                self.garden = redis.Redis()
                self.queuename = self.forkedpath('queue')
    
    @classmethod
    def get_id_triple(cls, name, obj):
        """
        Return an ID triple for an argument name and an object (as per providing_args).
        Modify this stuff if you need to use something else in a Redis queue.
        
        """
        if name in id_map:
            return cls.id_map[name](obj)
        return None
    
    @classmethod
    def get_modlclass(cls, app_label=None, modl_name=None):
        from django.db.models.loading import cache
        return cache.get_model(app_label, modl_name, seed_cache=True)
    
    @classmethod
    def get_object(cls, name, id_triple):
        app_label = id_triple[0]
        modl_name = id_triple[1]
        obj_id = id_triple[2]
        modlclass = cls.get_modlclass(app_label, modl_name)
        
        if hasattr(modlclass, 'objects') and name in id_remap:
            return cls.id_remap[name](modlclass, obj_id)
    
    def add_signal(self, signal_name, providing_args=['instance']):
        self.signals.update({
            signal_name: django.dispatch.Signal(providing_args=providing_args),
        })
    
    def connect(self, signal_name, callback, sender):
        if signal_name in self.signals:
            sig = self.signals.get(signal_name, None)
            if sig is not None:
                sig.connect(callback, sender=sender, dispatch_uid=callback)
                print 'Connected callback %s to signal %s from sender %s' % (callback, signal_name, sender)
                return
        raise AttributeError("Can't connect(): no signal named %s registered")
    
    def queue_add(self, queue_string):
        if self.garden:
            return self.garden.rpush(self.queuename, queue_string)
        return None
    
    def queue_grab(self):
        if self.garden:
            return self.garden.lpop(self.queuename)
        return None
    
    def queue_length(self):
        if self.garden:
            return self.garden.llen(self.queuename)
        return -1
    
    def send_now(self, name, sender, **kwargs):
        #print "send_now() called, signals[name] = %s, sender = %s, kwargs = %s" % (self.signals[name], sender, kwargs)
        if name in self.signals:
            self.signals[name].send_robust(sender=sender, **kwargs)
        return -2
    
    def enqueue(self, name, sender, **kwargs):
        if self.garden and (name in self.signals):
            queue_json = {
                'name': name,
                'sender': dict(app_label=sender._meta.app_label, modl_name=sender.__class__.__name__.lower()),
            }
            
            for k, v in kwargs.items():
                if k in KewGardens.id_map:
                    queue_json.update({
                        k: KewGardens.get_id_triple(v),
                    })
            
            return self.queue_add(json.dumps(queue_json))
    
    def retrieve(self):
        if self.queue_length() > 0:
            out = self.queue_grab()
            if out is not None:
                return json.loads(out)
        return None
    
    def dequeue(self, queued_signal=None):
        if not queued_signal:
            queued_signal = self.retrieve()
        
        if queued_signal is not None:
            name = queued_signal.pop('name')
            sender = KewGardens.get_modlclass(queued_signal.pop('sender'))
            kwargs = {}
            
            for k, v in queued_signal.items():
                kwargs.update({
                    k: KewGardens.get_object(v),
                })
            
            if name in self.signals:
                self.signals[name].send(sender=sender, **kwargs)
    
    def send(self, name, sender, **kwargs):
        #print "send() called, runmode = %s" % self.runmode
        
        if self.runmode:
            if self.runmode == imagekit.IK_ASYNC_REQUEST:
                # it's a web request -- enqueue it
                return self.enqueue(name, sender, **kwargs)
            elif self.runmode == imagekit.IK_ASYNC_DAEMON:
                # signal sent in daemon mode -- enqueue it
                return self.enqueue(name, sender, **kwargs)
            elif self.runmode == imagekit.IK_ASYNC_MGMT:
                # signal sent in command mode -- fire away
                return self.send_now(name, sender, **kwargs)
            else:
                # fire normally
                return self.send_now(name, sender, **kwargs)
        else:
            # fire normally
            return self.send_now(name, sender, **kwargs)
    
    """
    Override for __getattr__() allows standard signal connection like:
    
        signalqueue.pre_cache.connect()
    
    """
    def __getattr__(self, name):
        if name in self.signals:
            return self.signals[name]
        return object.__getattr__(name)
    
    """
    Iterator methods -- to dump the queue, do this:
    
        for qd in signalqueue:
            signalqueue.dequeue(queued_signal=qd)
    
    """
    def next(self):
        if not self.runmode:
            raise ValueError("Can't iterate through queue: no queue exists as imagekit.IK_RUNMODE isn't defined")
        
        if self.runmode == imagekit.IK_SYNC:
            raise ValueError("Can't iterate through queue in synchronous signal mode (IK_RUNMODE == imagekit.IK_SYNC)")
        
        if not self.queue_length() > 0:
            raise StopIteration
        
        return self.retrieve()
    
    def __iter__(self):
        return self

signalqueue = KewGardens()
signalqueue.add_signal('pre_cache')
signalqueue.add_signal('clear_cache')
signalqueue.add_signal('refresh_histogram')
signalqueue.add_signal('refresh_icc_data')
        