#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os, hashlib
from pprint import pprint
from django.db.models import Q
from django.db.models.loading import cache
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from imagekit.models import ImageWithMetadata, ICCModel
from imagekit.specs import ImageSpec
from imagekit.modelfields import *
from imagekit.utils import icchash

from . import echo_banner


class Command(BaseCommand):
    
    option_list = BaseCommand.option_list + (
        make_option('--ids', '-i', dest='ids',
            help="Optional range of IDs like low:high",
        ),
    )
    
    help = ('Updates all ImageKit cached profiles stored as ICCModels.')
    args = '[apps]'
    requires_model_validation = True
    can_import_settings = True
    
    def handle(self, *args, **options):
        echo_banner()
        return update_icc_cache(args, options)

def update_icc_cache(apps, options):
    """
    Updates the ICCModes data store with profiles harvested from ImageModel subclasses specified on the command line.
    
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
                        if issubclass(m, ImageWithMetadata):
                            modls.append(m)
                else:
                    putativemodel = cache.get_model(app_parts[0], app_parts[1])
                    if issubclass(putativemodel, ImageWithMetadata):
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
                    
                    print 'ICC Update: scanning %s objects in "%s.%s" for new ICC profile data...' % (objs.count(), app_parts[0], modl.__name__)
                    verb = int(options.get('verbosity', 1)) > 1
                    i = 0
                    ii = 0
                    
                    for obj in objs:
                        
                        if obj.icc:
                            
                            i += 1
                            if verb:
                                print ""
                                print ">>> %0d >>> %30s : %s %s" % (
                                    i,
                                    ((" " * 50) + obj._imgfield.name)[30:],
                                    obj.icc.getDescription(),
                                    '',
                                )
                            try:
                                ICCModel.objects.get(icchash__iexact=icchash(obj.icc))
                            
                            except ObjectDoesNotExist:
                                new_icc = ICCModel()
                                new_icc_file = ContentFile(obj.icc.data)
                                new_icc.iccfile.save(
                                    new_icc._storage.get_valid_name("%s.icc" % obj.icc.getDescription()),
                                    File(new_icc_file),
                                )
                                new_icc.save() # may be technically unnecessary
                                ii += 1
                                
                                if verb:
                                    print ">>> %0d >>> %s : %s" % (
                                        i,
                                        new_icc.iccfile.name,
                                        new_icc.icchash,
                                    )
                            
                            else:
                                if verb:
                                    print "--- %0d --- %s : %s %s" % (
                                        i,
                                        "                       (exists)",
                                        obj.icc.getDescription(),
                                        '',
                                    )
                    
                    if verb:
                        print ""
                        print "================================================================================="
                        
                        print "::: Examined %s objects." % len(objs)
                    print "::: Found %s possible profiles," % i
                    print "::: Committed %s unique instances of which to the database." % ii
                    
    else:
        print 'Please specify on or more app names'
