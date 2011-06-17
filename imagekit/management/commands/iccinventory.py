#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from imagekit.models import ICCModel, _storage
from imagekit.etc.profileinfo import profileinfo

class Command(BaseCommand):
    
    help = ('Prints out extensive logorrheic minutiae concerning the ICC profiles stored as ICCModels.')
    args = '[apps]'
    requires_model_validation = True
    can_import_settings = True

    def handle(self, *args, **options):
        #verb = int(options.get('verbosity', 1)) > 1
        # verbose by definition
        
        iccs = ICCModel.objects.all()
        
        print ""
        print "+++ django-imagekit by Justin Driscoll -- http://adevelopingstory.com/"
        print "+++ color management components by Alexander Böhn -- http://objectsinspaceandtime.com/"
        print "+++ profileinfo() and ICCProfile base class from DispcalGUI by Florian Höch -- http://dispcalgui.hoech.net/"
        
        print ""
        print ""
        print "ICC Inventory: %s unique ICCModel instances" % iccs.count()
        
        if iccs.count() < 1:
            print ""
            print "--- Profile store empty: add ICC profiles with ./manage.py iccupdate [app].<Model>"
            print "--- Or, upload your .icc files using the django admin"
            print ""
            return
        
        for icc in iccs:
            
            st = icc.iccfile.storage
            
            print ""
            print ">>> %d : %s" % (icc.pk, icc.iccfile.name)
            print ">>> %s" % st.url(icc.iccfile)
            print ""
            print "--- Created:   \t\t %s" % icc.createdate
            print "--- Altered:   \t\t %s" % icc.modifydate
            print "--- ICC Hash:  \t\t %s" % icc.icchash
            print "--- Profile Signature: \t %s" % icc.icc.getIDString()
            print ""
            print "--- Profile Info:"
            
            profileinfo(icc.icc)
            
            print ""
        
        
        
        