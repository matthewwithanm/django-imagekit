import sys, os
from pprint import pprint
from django.db.models import Q
from django.db.models.loading import cache
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ImproperlyConfigured
from optparse import make_option
from imagekit.models import ImageModel
from imagekit.specs import ImageSpec


class Command(BaseCommand):
    
    option_list = BaseCommand.option_list + (
        make_option('--ids', '-i', dest='ids',
            help="Optional range of IDs like low:high",
        ),
    )
    
    help = ('Clears all ImageKit cached image files.')
    args = '[apps]'
    requires_model_validation = True
    can_import_settings = True

    def handle(self, *args, **options):
        return flush_image_cache(args, options)

def flush_image_cache(apps, options):
    """
    Clears the image cache.
    """
    
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
                    
                    print 'Flushing image file cache for %s objects in "%s.%s"' % (objs.count(), app_parts[0], modl.__name__)
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
                                obj.save()
                                obj._pre_cache()
                        
                        else: # go quietly
                            obj.save()
                            obj._pre_cache()
                            
    else:
        print 'Please specify on or more app names'

