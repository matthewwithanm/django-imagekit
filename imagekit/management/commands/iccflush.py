#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os
from pprint import pprint
from django.db.models import Q
from django.db.models.loading import cache
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ImproperlyConfigured
from optparse import make_option
from imagekit.models import ICCImageModel
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
            modls = list()
            
            try:
                cache.load_app(app_parts[0])
                app = cache.get_app(app_parts[0])
            except ImproperlyConfigured:
                print "WTF: no app with label %s found" % app_parts[0]
            else:
                
                if len(app_parts) < 2:
                    for m in cache.app_models.get(app_parts[0].lower()).values():
                        if issubclass(m, ICCImageModel):
                            modls.append(m)
                else:
                    putativemodel = cache.get_model(app_parts[0], app_parts[1])
                    if issubclass(putativemodel, ICCImageModel):
                        modls.append(putativemodel)
                
                for modl in modls:
                    
                    buckets = dict()
                    profiles = dict()
                    
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
                    
                    print 'Recaching ICC profiles for %s objects in "%s.%s"' % (objs.count(), app_parts[0], modl.__name__)
                    for obj in objs:
                        
                        obj._clear_iccprofile()
                        obj.save(False)
                        
                        if obj.icc and int(options.get('verbosity', 1)) > 1:
                            
                            hsh = obj._icc_filehash
                            buckets[hsh] = buckets.get(hsh, 0) + 1
                            
                            if not profiles.get(hsh):
                                profiles[hsh] = "%s%s" % (
                                    obj._icc_profilename,
                                    obj._icc_productname and " (%s)" % obj._icc_productname or ''
                                )
                            
                            print u"""
>>>\t filename\t\t %s
+++\t file hash\t\t %s
+++\t color profile\t\t %s""" % (
                                unicode(obj._iccfilename),
                                unicode(hsh),
                                unicode("%s%s" % (
                                    obj._icc_profilename,
                                    obj._icc_productname and " (%s)" % obj._icc_productname or ''
                                )),
                            )
                    
                    if int(options.get('verbosity', 1)) > 1:
                        print "\nHASH TOTALS"
                        for k, v in buckets.items():
                            print "###\t\t\t %s\t %s" % (v, profiles[k])
                    
    else:
        print 'Please specify on or more app names'
