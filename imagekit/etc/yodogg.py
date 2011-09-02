#!/usr/bin/env python
# encoding: utf-8
"""
yodogg.py

Created by FI$H 2000 on 2011-09-02.
Copyright (c) 2011 Objects In Space And Time, LLC. All rights reserved.

"""

#import __main__ as __maine__
import __main__

import types, string
from pprint import pprint
from imagekit import processors
from imagekit.specs import ImageSpec

s = set()
d = dict()

for p in processors.__dict__.values():
    if type(p) in (types.ClassType, types.TypeType):
        if issubclass(p, processors.ImageProcessor):
            if p not in (processors.ImageProcessor, processors.Format, processors.ICCTransform, processors.ICCProofTransform):
                pname = "ProcessorTest%s" % string.capwords(p.__name__.replace('_', ' ')).replace(' ', '')
                sname = "SpecTest%s" % string.capwords(p.__name__.replace('_', ' ')).replace(' ', '')
                
                pbase = (p,)
                sbase = (ImageSpec,)
                stuff = { "__yodogg__": "I Heard You Like Metaprogramming", }
                specatts = {
                    "pre_cache":    True,
                    "access_as":    "%s_accessor" % p.__name__.replace(' ', '_').lower(),
                    "__yodogg__":   "So we put some class definitions in your class definitions",
                    
                }
                
                #__maine__.testproc = type(pname, pbase, stuff)
                #__maine__.testspec = type(sname, sbase, specatts)
                setattr(__main__, pname, type(pname, pbase, stuff))
                setattr(__main__, sname, type(sname, sbase, specatts))
                
                #s.add( (testproc, testspec) )


for tts in s:
    d.update({
        tts[0].__name__: [tts[0], tts[0].__base__, tts[1], tts[1].__base__],
    })

pprint(d)
print
pprint(s)

for ll in list(locals().values()) + list(globals().values()):
    if hasattr(ll, '__name__'):
        if ll.__name__.startswith("Processor") or ll.__name__.startswith("Spec"):
            print "YO DOGG! %s" % ll.__name__
        
