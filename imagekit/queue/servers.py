#!/usr/bin/env python
# encoding: utf-8
"""
servers.py

Created by FI$H 2000 on 2011-07-05.
Copyright (c) 2011 OST, LLC. All rights reserved.
"""

import sys
sys.path.append('/Users/fish/Dropbox/local-instance-packages/Django-1.3')
sys.path.append('/Users/fish/Dropbox/imagekit/django-imagekit-f2k')
sys.path.append('/Users/fish/Dropbox/nodebox-color/')
sys.path.append('/Users/fish/Dropbox/ost2')
sys.path.append('/Users/fish/Dropbox/ost2/ost2')
sys.path.append('/Users/fish/Dropbox/ost2/ost2/lib')

import hashlib, curses

from django.core.management import setup_environ
import settings
setup_environ(settings)

from django.conf import settings
from django.template import Context, loader
import tornado.options
import tornado.web
import tornado.websocket
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.options import define, _LogFormatter

#from imagekit.signals import signalqueue as ik_signal_queue
#from imagekit.signals import KewGardens
from imagekit.utils import logg
from imagekit.utils.json import json
from imagekit.queue import queues
from imagekit.queue.poolqueue import PoolQueue
import logging
#import imagekit

define('port', default=settings.IK_QUEUE_SERVER_PORT, help='Queue server HTTP port', type=int)

class Application(tornado.web.Application):
    def __init__(self, **kwargs):
        from django.core.management import setup_environ
        import settings
        setup_environ(settings)
        from django.conf import settings
        
        nm = kwargs.get('queue_name', "default")
        
        handlers = [
            (r'/', MainHandler),
            (r'/status', QueueServerStatusHandler),
            (r'/sock/status', QueueStatusSock),
        ]
        
        settings = dict(
            template_path=settings.TEMPLATE_DIRS[0],
            static_path=settings.MEDIA_ROOT,
            xsrf_cookies=True,
            cookie_secret=hashlib.sha1(settings.SECRET_KEY).hexdigest(),
            logging='info',
            queue_name=nm,
        )
        
        tornado.web.Application.__init__(self, handlers, **settings)
        self.queues = {}
        if nm is not None:
            self.queues.update({
                nm: PoolQueue(queue_name=nm, active=True)
            })


class BaseQueueConnector(object):
    
    def queue(self, queue_name='default'):
        if queue_name not in queues.keys():
            raise IndexError("No queue named %s is defined" % queue_name)
        
        if not queue_name in self.application.queues:
            self.application.queues[queue_name] = PoolQueue(queue_name=queue_name, active=False)
        
        return self.application.queues[queue_name]
    
    @property
    def defaultqueue(self):
        return self.queue('default')
    
    def clientlist_get(self):
        if not hasattr(self.application, 'clientlist'):
            self.application.clientlist = []
        return self.application.clientlist
    def clientlist_set(self, val):
        self.application.clientlist = val
    
    clientlist = property(clientlist_get, clientlist_set)
    

class QueueStatusSock(tornado.websocket.WebSocketHandler, BaseQueueConnector):
    def open(self):
        self.clientlist.append(self)
    
    def on_message(self, inmess):
        mess = json.loads(str(inmess))
        nm = mess.get('status', "default")
        self.write_message({
            nm: self.queue(nm).signalqueue.queue_length(),
        })
    
    def on_close(self):
        if self in self.clientlist:
            self.clientlist.remove(self)

class BaseHandler(tornado.web.RequestHandler, BaseQueueConnector):
    pass

class MainHandler(BaseHandler):
    def get(self):
        self.write("YO DOGG!")

class QueueServerStatusHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        super(QueueServerStatusHandler, self).__init__(*args, **kwargs)
        self.template = loader.get_template('queueserver/status.html')
    
    def get(self):
        nm = self.get_argument('queue', "default")
        self.write(
            self.template.render(Context({
                'queue_name': nm,
                'items': [json.loads(morsel) for morsel in self.queue(nm).signalqueue.garden.values()],
            }))
        )



def main():
    logg = logging.getLogger("imagekit")
    # Set up color if we are in a tty and curses is installed
    
    color = False
    if curses and sys.stderr.isatty():
        try:
            curses.setupterm()
            if curses.tigetnum("colors") > 0:
                color = True
        except:
            pass
    channel = logging.StreamHandler()
    channel.setFormatter(_LogFormatter(color=color))
    logg.addHandler(channel)
    
    logg.info("YO DOGG.")
    
    try:
        tornado.options.parse_command_line()
        http_server = HTTPServer(Application())
        
        #http_server.bind(settings.IK_QUEUE_SERVER_PORT)
        #http_server.start(num_processes=10) # Forks multiple sub-processes
        http_server.listen(settings.IK_QUEUE_SERVER_PORT)
        IOLoop.instance().start()
        
    except KeyboardInterrupt:
        print 'NOOOOOOOOOOOO DOGGGGG!!!'


if __name__ == '__main__':
    from django.core.management import setup_environ
    import settings
    setup_environ(settings)
    from django.conf import settings
    
    main()
    


