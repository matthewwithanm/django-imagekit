#!/usr/bin/env python
# encoding: utf-8
from django.db.models import Q
from django.db.models.loading import cache
from django.core.management.base import BaseCommand
from django.core.exceptions import ImproperlyConfigured
from optparse import make_option

from . import echo_banner


class Command(BaseCommand):
    
    option_list = BaseCommand.option_list + (
        make_option('--ids', '-i', dest='ids',
            help="""
            Optional range of IDs, like low:high
            """,
        ),
        make_option('--runmode', '-r', dest='runmode',
            default='SQ_SYNC',
            help="""
            Runmode for ImageKit's signal queue. Default is synchronous execution --
            SQ_SYNC; use SQ_ASYNC_MGMT or SQ_ASYNC_REQUEST for async execution.
            """,
        ),
        make_option('--queuename', '-q', dest='queue_name',
            default='default',
            help="""
            Name of the signal queue for ImageKit to use. If not specified, the default queue will be used.
            """,
        ),
        make_option('--keep-cache', '-C', action="store_false", dest='clear_cache',
            default=True,
            help="""
            Do not clear ImageKit-generated cached images. The default is to clear the cache.
            Using this option will not affect non-image ImageKit properties
            (e.g. Histograms, ICCMetaFields, et al)
            """,
        ),
    )
    
    help = ('Clears all ImageKit cached image files.')
    args = '[apps]'
    requires_model_validation = True
    can_import_settings = True
    
    def handle(self, *args, **options):
        
        echo_banner()
        
        import signalqueue
        signalqueue.autodiscover()
        
        from signalqueue import SQ_RUNMODES as runmodes
        from signalqueue.worker import backends
        from imagekit import signals as iksignals
        
        runmode_name = options.get('runmode').upper()
        queue_name = options.get('queuename', "default")
        queues = backends.ConnectionHandler(django_settings.SQ_QUEUES, runmodes.get(runmode_name))
        signalqueue = queues[queue_name]
        
        return flush_image_cache(args, signalqueue, options)

def flush_image_cache(apps, signalqueue, options):
    """
    Clears the ImageKit cache by iterating through the named apps,
    and re-saving the ImageModel subclasses it defines.
    
    Command-line options can be set to prevent the call to clear_cache()
    prior to the save() call.
    
    """
    from imagekit.models import ImageModel
    from imagekit.signals import KewGardens
    import imagekit
    
    apps = [a.strip(',') for a in apps]
    
    if apps:
        for app_label in apps:
            
            app_parts = app_label.split('.')
            modls = list()
            
            try:
                app = cache.get_app(app_parts[0])
            except ImproperlyConfigured:
                print "WTF: no app with label %s found" % app_parts[0]
            else:
            
                if not len(app_parts) == 2:
                    modls = [m for m in cache.get_models(app) if issubclass(m, ImageModel)]
                else:
                    putativemodel = cache.get_model(app_parts[0], app_parts[1])
                    if issubclass(putativemodel, ImageModel):
                        modls.append(putativemodel)
                
                clear_cache = options.get('clear_cache', True)
                print '>>> Cached ImageKit images will be %s.' % (clear_cache and "deleted" or "preserved")
                
                # set the runmode, if provided
                if options.get("runmode").upper().startswith("SQ_ASYNC_"):
                    print '>>> Dequeueing signals in runmode %s from the queue "%s".' % (
                        options.get("runmode").upper(),
                        signalqueue.queue_name,
                    )
                else:
                    print '>>> Running in synchronous mode -- not using a signal queue.'
                
                
                print ''
                
                for modl in modls:
                    
                    objs = modl.objects.all()
                    
                    if options.get('ids'):
                        
                        if options.get('ids').find(':') == -1:
                        
                            objs = objs.filter(
                                Q(id__gte=0) & Q(id__lte=int(options.get('ids')))
                            )
                        
                        else:
                            
                            bottom, top = options.get('ids').split(':')
                            if not bottom:
                                bottom = '0'
                            if not top:
                                objs = objs.filter(
                                    Q(id__gte=int(bottom))
                                )
                            else:
                                objs = objs.filter(
                                    Q(id__gte=int(bottom)) & Q(id__lte=int(top))
                                )
                    
                    print '>>> Flushing image file cache for %s objects in "%s.%s"' % (objs.count(), app_parts[0], modl.__name__)
                    
                    for obj in objs:
                        
                        if int(options.get('verbosity', 1)) > 1:
                            try:
                                if obj._imgfield.name:
                                    print ">>>\t %s" % obj._imgfield.name or "(NO NAME)"
                                else:
                                    print "---\t name (None)"
                                if obj._imgfield.size:
                                    print ">>>\t %s %s" % (obj._imgfield.size or "(NO SIZE)", obj.tophex())
                                else:
                                    print "---\t size (None)"
                            except:
                                print "xxx\t EXCEPTION"
                            else:
                                if clear_cache:
                                    obj.clear_cache()
                                obj.save()
                        
                        else: # go quietly
                            if clear_cache:
                                obj.clear_cache()
                            obj.save()
                            
    else:
        print '+++ Please specify one or more app names'

