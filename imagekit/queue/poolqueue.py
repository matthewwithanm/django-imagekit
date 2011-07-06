#!/usr/bin/env python
# encoding: utf-8
"""
poolqueue.py

Created by FI$H 2000 on 2011-07-05.
Copyright (c) 2011 OST, LLC. All rights reserved.
"""

from django.core.management import setup_environ
import settings
setup_environ(settings)

from django.conf import settings
from tornado.ioloop import IOLoop, PeriodicCallback

from imagekit.signals import signalqueue as ik_signal_queue
from imagekit.signals import KewGardens
#from imagekit.utils import logg
from imagekit.utils.json import json
import imagekit
import logging

logg = logging.getLogger(__name__)

class PoolQueue(object):
    
    def __init__(self, *args, **kwargs):
        super(PoolQueue, self).__init__()
        self.active = kwargs.pop('active', True)
        self.interval = kwargs.pop('interval', 1)
        
        self.signalqueue = KewGardens(
            runmode=imagekit.IK_ASYNC_DAEMON, # running in daemon mode
            signals=ik_signal_queue.signals,
            queue_name=kwargs.get('queue_name', "default"),
        )
        
        if self.interval > 0:
            self.shark = PeriodicCallback(self.cueball, self.interval*10)
        
        if self.active:
            self.shark.start()
    
    def stop(self):
        self.active = False
        self.shark.stop()
    
    def rerack(self):
        self.active = True
        self.shark.start()
    
    def cueball(self):
        queued_signal = self.signalqueue.retrieve()
        if queued_signal is not None:
            #logg.info("dequeueing signal: %s" % queued_signal)
            name = queued_signal.pop('name')
            enqueue_runmode = queued_signal.pop('enqueue_runmode', imagekit.IK_ASYNC_REQUEST)
            sender = KewGardens.get_modlclass(**queued_signal.pop('sender'))
            kwargs = { 
                'dequeue_runmode': self.signalqueue.runmode,
                'enqueue_runmode': enqueue_runmode,
            }
            
            for k, v in queued_signal.items():
                if type(v) == dict:
                    kwargs.update({
                        k: KewGardens.get_object(k, v),
                    })
            
            if name in self.signalqueue.signals:
                self.signalqueue.signals[name].send(sender=sender, **kwargs)
