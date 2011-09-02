#!/usr/bin/env python
# encoding: utf-8
"""
iheardyoulikemetaprogramming.py

Created by FI$H 2000 on 2011-09-02.
Copyright (c) 2011 Objects In Space And Time, LLC. All rights reserved.

"""
from imagekit.etc import yodogg


for ll in list(locals().values()) + list(globals().values()):
    if hasattr(ll, '__name__'):
        if ll.__name__.startswith("Processor") or ll.__name__.startswith("Spec"):
            print "YO DOGG! %s" % ll.__name__
        
