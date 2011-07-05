#!/usr/bin/env python
# encoding: utf-8
"""
signals.py

Implements KewGarden, a frontend class for the imagekit async queue that manages and intercepts
imagekit's custom django signals, enabling them to execute asynchronously. This module contains
an instance of KewGarden, signalqueue, which provides a signal interface similar to native django:

    from imagekit.signals import signalqueue
    
    # add a new signal
    signalqueue.add_signal('custom_signal')
    
    # add a new signal with custom providing args
    signalqueue.add_signal('another_signal', providing_args=['instance', 'flag'])
    
    # connect a receiver to your signals
    signalqueue.connect('another_signal', another_callback, sender=SomeOtherClass)
    signalqueue.custom_signal.connect(callback_function, sender=SomeClass) # alternative syntax
    
    # send your signals synchronously with a blocking call
    signalqueue.send('another_signal', sender=AnotherClass, instance=an_instance)
    signalqueue.another_signal.send(sender=AnotherClass, instance=an_instance) # alternative syntax
    
    # enqueue signals and return immediately
    signalqueue.enqueue('custom_signal', sender=SomeClass, instance=an_instance)
    signalqueue.enqueue('another_signal', sender=SomeClass, instance=an_instance, flag='yo dogg')
    
    # send either asynchronously (returning immediately) or synchronously (blocking),
    # depending on your IK_RUNMODE setting
    signalqueue.send('custom_signal', sender=SomeClass, instance=an_instance)
    signalqueue.send('another_signal', sender=SomeClass, instance=an_instance, flag='yo dogg')
    

You configure your queue in your settings.py file much as you would your databases
or hackstack engines, like so:

    IK_RUNMODE = imagekit.IK_ASYNC_REQUEST
    IK_QUEUES = {
        'default': {                                    # you need at least one dict named 'default' in IK_QUEUES
            'NAME': 'your_queue_name',                  # optional - defaults to 'imagekit_queue'
            'ENGINE': 'imagekit.backends.SomeQueue',    # required - full path to a QueueBase subclass
            'OPTIONS': {                                # most likely required - these are specific to
                'host': 'localhost',                    # the queue implementation you're using.
                'port': 7707,
            }
        }
    }

The NAME setting is different than the dict label ('default' in the above) --
NAME is used by the queue implementation internally, and may be subject to restrictions
as per the queue's requirements (e.g., RedisQueue NAMEs should be alphanumeric ascii strings
that don't start with numbers). Whereas aside from the mandatory 'default', your labels can
be whatever you want.

Anything in OPTIONS gets handed off to the queue implementation and putatively used as the
queue's internals go about their business. See the QueueBase subclasses below for examples.

In addition, IK_RUNMODE should be set to one of these values (defined in imagekit/__init__.py):

    * IK_SYNC -- All signals will execute synchronously. Calls block until they return
    * IK_ASYNC_REQUEST -- Signals sent with signalqueue.send() and signalqueue.enqueue()
                          execute asynchronously. Calls using these methods return immediately.

(Don't use the other two constants, IK_ASYNC_MGMT and IK_ASYNC_DAEMON. Those are used internally
to designate calls that are sent in the management command and queue daemon contexts, respectively.)

Created by FI$H 2000 on 2011-06-29.
Copyright (c) 2011 OST, LLC. All rights reserved.

"""

import hashlib, uuid, PIL
import django.dispatch
from django.conf import settings
from django.db.models.loading import cache
from imagekit.utils.json import json
import imagekit

class KewGardens(object):
    forkingpaths = {}
    queue_name = "default"
    
    id_map = {
        'instance': lambda obj: { 'obj_id': obj.pk, 'app_label': obj._meta.app_label, 'modl_name': obj.__class__.__name__.lower(), },
        'iccdata': lambda iccdata: { 'obj_id': hashlib.sha1(iccdata.data).hexdigest(), 'app_label': 'imagekit', 'modl_name': 'iccmodel', },
        'spec_name': lambda spec_name: { 'obj_id': spec_name, 'app_label': 'python', 'modl_name': 'str', },
    }
    
    id_remap = {
        'instance': lambda modlcls, pk: modlcls.objects.get(pk=pk),
        'iccdata': lambda modlcls, hsh: modlcls.objects.profile_match(hsh=hsh).icc,
        'spec_name': lambda modlcls, spec_name: spec_name,
    }
    
    def __init__(self, *args, **kwargs):
        runmode = kwargs.pop('runmode', None)
        self.signals = kwargs.pop('signals', {})
        self.queue_name = kwargs.pop('queue_name', "default")
        super(KewGardens, self).__init__(*args, **kwargs)
        
        if not runmode:
            runmode = settings.IK_RUNMODE
        self.runmode = runmode
        
        if not self.runmode == imagekit.IK_SYNC:
            # running with asynchronous calls -- set up access to queues
            from imagekit.queue import queues
            self.forkingpaths = queues
    
    @classmethod
    def get_id_dict(cls, name, obj):
        if name in cls.id_map:
            return cls.id_map[name](obj)
        return None
    
    @classmethod
    def get_modlclass(cls, app_label, modl_name):
        return cache.get_model(str(app_label), str(modl_name))
    
    @classmethod
    def get_object(cls, name, id_dict):
        obj_id = id_dict.get('obj_id')
        modlclass = cls.get_modlclass(
            app_label=id_dict.get('app_label'),
            modl_name=id_dict.get('modl_name'),
        )
        if name in cls.id_remap:
            return cls.id_remap[name](modlclass, obj_id)
        return None
    
    @property
    def garden(self):
        try:
            return self.forkingpaths[self.queue_name]
        except ValueError:
            return None
    
    def add_signal(self, signal_name, providing_args=['instance']):
        self.signals.update({
            signal_name: django.dispatch.Signal(providing_args=providing_args),
        })
    
    def connect(self, signal_name, callback, sender):
        if signal_name in self.signals:
            sig = self.signals.get(signal_name, None)
            if sig is not None:
                sig.connect(callback, sender=sender, dispatch_uid=callback)
                return
        
        raise AttributeError("Can't connect(): no signal '%s' registered amongst: %s" % (signal_name, str(self.signals.keys())))
    
    def queue_add(self, queue_string):
        if self.garden:
            return self.garden.push(queue_string)
        return None
    
    def queue_grab(self):
        if self.garden:
            return self.garden.pop()
        return None
    
    def queue_length(self):
        if self.garden:
            return self.garden.count()
        return -1
    
    def queue_values(self, floor=0, ceil=-1):
        if self.garden:
            return self.garden.values(floor, ceil)
        return []
    
    def send_now(self, name, sender, **kwargs):
        #print "send_now() called, signals[name] = %s, sender = %s, kwargs = %s" % (self.signals[name], sender, 'kwargs')
        if name in self.signals:
            self.signals[name].send_robust(sender=sender, **kwargs)
        return -2
    
    def enqueue(self, name, sender, **kwargs):
        if self.garden and (name in self.signals):
            queue_json = {
                'name': name,
                'sender': dict(app_label=sender._meta.app_label, modl_name=sender._meta.object_name.lower()),
            }
            
            for k, v in kwargs.items():
                if k in KewGardens.id_map:
                    queue_json.update({
                        k: KewGardens.get_id_dict(k, v),
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
        
        print "dequeueing signal: %s" % queued_signal
        
        if queued_signal is not None:
            name = queued_signal.pop('name')
            sender = KewGardens.get_modlclass(**queued_signal.pop('sender'))
            kwargs = { 'dequeue_runmode': self.runmode, }
            
            for k, v in queued_signal.items():
                kwargs.update({
                    k: KewGardens.get_object(k, v),
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
    Override for __getattr__() allows signal connection a la the standard Django signal syntax,
    like so:
    
        signalqueue.pre_cache.connect()
    
    """
    def __getattr__(self, name):
        if name in self.signals:
            return self.signals[name]
        return object.__getattribute__(self, name)
    
    """
    Iterator methods.
    
    To dequeue and send all the currently-enqueued signals, you can do this:
    
        for qd in signalqueue:
            signalqueue.dequeue(queued_signal=qd)
    
    Currently, these methods are slightly misnamed, as calling next() will actually
    dequeue the signal. In the example above, next() is called behind-the-scenes
    to furnish the 'qd' variable by popping a signal out of the queue. The subsequent 
    call to dequeue() sends the signal after the fact -- it doesn't modify the contents
    of the queue.
    
    To fix this, we'll have to make next() access the queue without popping, and 
    add a method to imagekit.queue.backends.QueueBase to allow arbitrary queue
    members to get dequeued. This will all happen... IN THE FUTURE!!
    
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
signalqueue.add_signal('prepare_spec', providing_args=['instance', 'spec_name'])
signalqueue.add_signal('delete_spec', providing_args=['instance', 'spec_name'])

signalqueue.add_signal('refresh_icc_data')
signalqueue.add_signal('refresh_exif_data')
signalqueue.add_signal('save_related_histogram')
signalqueue.add_signal('refresh_histogram_channel', providing_args=['instance', 'channel_name'])
