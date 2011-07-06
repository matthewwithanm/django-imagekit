#!/usr/bin/env python
# encoding: utf-8
import sys, os
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ImproperlyConfigured
from pprint import pformat
from optparse import make_option
from imagekit.signals import signalqueue, KewGardens
import imagekit

class Command(BaseCommand):
    
    option_list = BaseCommand.option_list + (
        make_option('--queue-name', '-n', dest='queue_name', default='default',
            help="Name of queue, as specified in settings.py (defaults to 'default')",
        ),
    )
    
    help = ('Flushes the ImageKit queue, executing all enqueued signals.')
    requires_model_validation = True
    can_import_settings = True
    
    def handle(self, *args, **options):
        echo_banner()
        try:
            return flush_imagekit_queue(args, options)
        except ImproperlyConfigured, err:
            print "*** ERROR in configuration: %s" % err
            print "*** Check the Imagekit options in your settings.py."

def echo_banner():
    print ""
    print "+++ django-imagekit by Justin Driscoll -- http://adevelopingstory.com/"
    print u"+++ color management components by Alexander Böhn -- http://objectsinspaceandtime.com/"
    print u"+++ profileinfo() and ICCProfile base class from DispcalGUI by Florian Höch -- http://dispcalgui.hoech.net/"
    print ""


def flush_imagekit_queue(apps, options):
    """
    Flushes the ImageKit queue, executing all enqueued signals.
    
    """
    signalmgr = KewGardens(
        runmode=imagekit.IK_ASYNC_MGMT, # running in management mode
        signals=signalqueue.signals,
        queue_name=options.get('queue_name', "default"),
    )
    
    print ">>> Flushing signal queue '%s' -- %s enqueued signals total" % (signalmgr.queue_name, signalmgr.queue_length())
    print ""
    
    if signalmgr.queue_length() > 0:
        for signalblip in signalmgr:
            #print ">>> Signal: "
            #print pformat(signalblip)
            
            obj_dict = signalblip.get('instance')
            obj = KewGardens.get_object('instance', obj_dict)
            
            print ">>> Processing signal for %s object: %s (%s)" % (obj.__class__.__name__, obj, obj.pk)
            
            signalmgr.dequeue(queued_signal=signalblip)
            
            print ""
            break
    
    
    print ">>> Done flushing signal queue '%s' -- %s enqueued signals remaining" % (signalmgr.queue_name, signalmgr.queue_length())
    print ""
    

