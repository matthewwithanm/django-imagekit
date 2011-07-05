#!/usr/bin/env python
# encoding: utf-8
"""
servers.py

Created by FI$H 2000 on 2011-07-05.
Copyright (c) 2011 OST, LLC. All rights reserved.
"""

import sys, os, hashlib
from django.core.management import setup_environ
import settings
setup_environ(settings)

from django.conf import settings
from django.template import Context, RequestContext, loader
from django.template.loader import render_to_string

import tornado.options
import tornado.web
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.options import define, options

from imagekit.signals import signalqueue as ik_signal_queue
from imagekit.signals import KewGardens
from imagekit.utils import logg
from imagekit.utils.json import json
from imagekit.queue.poolqueue import PoolQueue
import imagekit

define('port', default=settings.IK_QUEUE_SERVER_PORT, help='Queue server HTTP port', type=int)


class Application(tornado.web.Application):
    def __init__(self):
        from django.core.management import setup_environ
        import settings
        setup_environ(settings)
        from django.conf import settings
        
        handlers = [
            (r'/', MainHandler),
            (r'/status', QueueServerStatusHandler),
        ]
        
        settings = dict(
            template_path=settings.TEMPLATE_DIRS[0],
            static_path=settings.MEDIA_ROOT,
            xsrf_cookies=True,
            cookie_secret=hashlib.sha1(settings.SECRET_KEY).hexdigest(),
        )
        
        tornado.web.Application.__init__(self, handlers, **settings)
        self.db = None


class BaseHandler(tornado.web.RequestHandler):
    
    @property
    def asyncqueue(self):
        if not hasattr(self.application, 'asyncqueue'):
            self.application.asyncqueue = PoolQueue(
                active=True,
                interval=180, # 3 minutes
            )
        return self.application.asyncqueue

class MainHandler(BaseHandler):
    def get(self):
        self.write("YO DOGG!")

class QueueServerStatusHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        super(QueueServerStatusHandler, self).__init__(*args, **kwargs)
        self.template = loader.get_template('queueserver/status.html')
    
    def get(self):
        self.write(
            self.template.render(Context({
                'items': [json.loads(morsel) for morsel in self.asyncqueue.signalqueue.garden.values()]
            }))
        )


def main():
    logg.info("YO DOGG.")
    
    try:
        tornado.options.parse_command_line()
        http_server = HTTPServer(Application())
        http_server.bind(settings.IK_QUEUE_SERVER_PORT)
        http_server.start(0) # Forks multiple sub-processes
        IOLoop.instance().start()
    except KeyboardInterrupt:
        print 'NOOOOOOOOOOOO DOGGGGG!!!'


if __name__ == '__main__':
    from django.core.management import setup_environ
    import settings
    setup_environ(settings)
    from django.conf import settings
    
    main()

