import sys, os
from pprint import pprint
from django.db.models import Q
from django.db.models.loading import cache
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ImproperlyConfigured
from optparse import make_option
from imagekit.models import ImageModel, ICCImageModel
from imagekit.specs import ImageSpec
from imagekit.modelfields import *

class Command(BaseCommand):
    
    option_list = BaseCommand.option_list + (
        make_option('--ids', '-i', dest='ids',
            help="Optional range of IDs like low:high",
        ),
    )
    
    help = ('Clears all ImageKit cached ICC profiles.')
    args = '[apps]'
    requires_model_validation = True
    can_import_settings = True

    def handle(self, *args, **options):
        return flush_icc_cache(args, options)

def flush_icc_cache(apps, options):
    """
    Clears the ICC profile cache
    """
    
    apps = [a.strip(',') for a in apps]
    
    if apps:
        for app_label in apps:
            
            app_parts = app_label.split('.')
            models = list()
            
            
            try:
                app = cache.get_app(app_parts[0])
            except ImproperlyConfigured:
                print "WTF: no app with label %s found" % app_parts[0]
            else:
                
                if not len(app_parts) == 2:
                    models = [m for m in cache.get_models(app) if issubclass(m, ImageModel)]
                else:
                    putativemodel = cache.get_model(app_parts[0], app_parts[1])
                    if issubclass(putativemodel, ICCImageModel):
                        models.append(putativemodel)
                
                for model in models:
                    print 'Flushing ICC profile cache for %s objects in "%s.%s"\n' % (model.objects.all().count(), app_parts[0], model.__name__)
                    
                    buckets = dict()
                    profiles = dict()
                    
                    if not options.get('ids'):
                        objs = model.objects.all()
                    else:
                        if options.get('ids').find(':') == -1:
                        
                            objs = model.objects.filter(
                                Q(id__gte=0) & Q(id__lte=int(options.get('ids')))
                            )
                        
                        else:
                            
                            bottom, top = options.get('ids').split(':')
                            if not bottom:
                                bottom = '0'
                            if not top:
                                objs = model.objects.filter(
                                    Q(id__gte=int(bottom))
                                )
                            else:
                                objs = model.objects.filter(
                                    Q(id__gte=int(bottom)) & Q(id__lte=int(top))
                                )
                    
                    print 'Flushing image file cache for %s objects in "%s.%s"' % (objs.count(), app_parts[0], model.__name__)
                    for obj in objs.order_by('modifydate'):
                        
                        obj._clear_iccprofile()
                        whathappened = obj._save_iccprofile()
                        
                        if whathappened and int(options.get('verbosity', 1)) > 1:
                            
                            hsh = obj._icc_filehash
                            buckets[hsh] = buckets.get(hsh, 0) + 1
                            profiles[hsh] = obj._icc_productname
                            
                            print u"""
>>>\t filename\t\t %s
+++\t file hash\t\t %s
+++\t color profile\t\t %s""" % (
                                unicode(obj._iccfilename),
                                unicode(hsh),
                                unicode(obj._icc_productname),
                            )
                    
                    if int(options.get('verbosity', 1)) > 1:
                        print "\nHASH TOTALS"
                        for k, v in buckets.items():
                            print "###\t\t\t %s\t %s" % (v, profiles[k])
                    
    else:
        print 'Please specify on or more app names'
