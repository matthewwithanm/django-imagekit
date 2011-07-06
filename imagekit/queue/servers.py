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

import os, hashlib, curses

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
from tornado.options import define, options, _LogFormatter

from imagekit.signals import signalqueue as ik_signal_queue
from imagekit.signals import KewGardens
#from imagekit.utils import logg
from imagekit.utils.json import json
from imagekit.queue.poolqueue import PoolQueue
import logging
import imagekit

define('port', default=settings.IK_QUEUE_SERVER_PORT, help='Queue server HTTP port', type=int)
#logg = logging.getLogger(__name__)

class Application(tornado.web.Application):
    def __init__(self):
        from django.core.management import setup_environ
        import settings
        setup_environ(settings)
        from django.conf import settings
        
        handlers = [
            (r'/', MainHandler),
            (r'/status', QueueServerStatusHandler),
            (r'/queue', VisualQueueHandler),
        ]
        
        settings = dict(
            template_path=settings.TEMPLATE_DIRS[0],
            static_path=settings.MEDIA_ROOT,
            xsrf_cookies=True,
            cookie_secret=hashlib.sha1(settings.SECRET_KEY).hexdigest(),
            logging='info',
        )
        
        tornado.web.Application.__init__(self, handlers, **settings)
        #self.asyncqueue = None


class BaseHandler(tornado.web.RequestHandler):
    
    @property
    def asyncqueue(self):
        if not hasattr(self.application, 'asyncqueue'):
            self.application.asyncqueue = PoolQueue(
                active=True,
                interval=30, # 3 minutes
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

class VisualQueueHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        super(VisualQueueHandler, self).__init__(*args, **kwargs)
        #self.template = loader.get_template('queueserver/status.html')
        self.tophalf = loader.get_template('queueserver/tophalf.html')
        self.bottomhalf = loader.get_template('queueserver/bottomhalf.html')
        self.morsel = loader.get_template_from_string("""
            <tr>
                {% for key, thingy in item.items %}
                    {% if key == 'instance' %}
                        {% if thingy.thumbelina %}
                            <td>
                                {{ key }}: <img src="{{ thingy.thumbelina.url }}" />
                            </td>
                        {% else %}
                            <td>
                                {{ key }}: <span{% if key == 'name' %} class="big"{% endif %}>{{ thingy }}</span>
                            </td>
                        {% endif %}
                    {% else %}
                        <td>
                            {{ key }}: <span{% if key == 'name' %} class="big"{% endif %}>{{ thingy }}</span>
                        </td>
                    {% endif %}
                {% endfor %}
            </tr>
        """)
        
    
    @tornado.web.asynchronous
    def get(self):
        
        raw_items = [json.loads(morsel) for morsel in self.asyncqueue.signalqueue.garden.values()[:40]]
        items = []
        
        self.write(self.tophalf.render(Context({
            'somenumber': len(raw_items)
        })))
        
        for raw_item in raw_items:
            item = {}
            for k, v in raw_item.items():
                if k == 'name':
                    item.update({
                        'name': v,
                    })
                elif k == 'sender':
                    item.update({
                        'sender': KewGardens.get_modlclass(**v)
                    })
                else:
                    item.update({
                        k: KewGardens.get_object(k, v)
                    })
            #items.append(item)
            self.write(
                self.morsel.render(Context({
                    'item': item,
                }))
            )
        
        self.write(
            self.bottomhalf.render(Context({}))
        )
        self.finish()


def main():
    logg = logging.getLogger(__name__)
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
        http_server.bind(settings.IK_QUEUE_SERVER_PORT)
        http_server.start(num_processes=10) # Forks multiple sub-processes
        IOLoop.instance().start()
    except KeyboardInterrupt:
        print 'NOOOOOOOOOOOO DOGGGGG!!!'


if __name__ == '__main__':
    from django.core.management import setup_environ
    import settings
    setup_environ(settings)
    from django.conf import settings
    
    main()

