#!/usr/bin/env python
# encoding: utf-8
import sys, os
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ImproperlyConfigured
from pprint import pformat
from optparse import make_option
from imagekit.signals import signalqueue, KewGardens
import imagekit

from . import echo_banner


class Command(BaseCommand):
    
    option_list = BaseCommand.option_list + (
        make_option('--queuename', '-n', dest='queue_name', default='default',
            help="Name of queue, as specified in settings.py (defaults to 'default')",
        ),
    )
    
    help = ('Runs the ImageKit Tornado-based queue server.')
    args = '[optional port number, or ipaddr:port]'
    can_import_settings = True
    
    def echo(self, *args, **kwargs):
        """
        Print in color to stdout.
        
        """
        text = " ".join([str(item) for item in args])
        
        if settings.DEBUG:
            color = kwargs.get("color",32)
            self.stdout.write("\033[0;%dm%s\033[0;m" % (color, text))
        
        else:
            print text
    
    def run_queue_server(self, args, options):
        """
        Runs the ImageKit Tornado-based queue server.
        
        """
        import tornado.options
        from tornado.httpserver import HTTPServer
        from tornado.ioloop import IOLoop
        from imagekit.queue.servers import Application
        
        http_server = HTTPServer(Application(queue_name=options.get('queue_name')))
        http_server.listen(int(options.get('port')), address=options.get('addr'))
        
        try:
            IOLoop.instance().start()
        
        except KeyboardInterrupt:
            self.echo("\nShutting down ImageKit queue server ...\n", color=31)
        
        finally:
            self.echo("+++ Exiting ...\n", color=16)
            sys.exit(0)
        
    
    def handle(self, addrport='', *args, **options):
        #echo_banner()
        
        if args:
            raise CommandError('Usage: %s %s' % (__file__, self.args))
        
        if not addrport:
            addr = ''
            port = str(settings.IK_QUEUE_SERVER_PORT) or '8000'
        else:
            try:
                addr, port = addrport.split(':')
            except ValueError:
                addr, port = '', addrport
        
        if not addr:
            addr = '127.0.0.1'
        
        if not port.isdigit():
            raise CommandError("%r is not a valid port number." % port)
        
        self.quit_command = (sys.platform == 'win32') and 'CTRL-BREAK' or 'CONTROL-C'
        
        options.update({
            'addr': addr,
            'port': port,
        })
        
        self.echo("Validating models...\n")
        self.validate(display_num_errors=True)
        
        self.echo(("\nDjango version %(version)s, using settings %(settings)r\n"
                   "Queue \"%(queue_name)s\" running at http://%(addr)s:%(port)s/\n"
                   "Quit the server with %(quit_command)s.\n" ) % {
                        "version": self.get_version(),
                        "settings": settings.SETTINGS_MODULE,
                        "queue_name": options.get('queue_name'),
                        "addr": addr,
                        "port": port,
                        "quit_command": self.quit_command,
                    })
        
        
        try:
            self.run_queue_server(args, options)
        
        except ImproperlyConfigured, err:
            self.echo("*** ERROR in configuration: %s" % err, color=31)
            self.echo("*** Check the Imagekit options in your settings.py.", color=31)
