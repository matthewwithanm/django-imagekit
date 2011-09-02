#!/usr/bin/env python
# encoding: utf-8
"""
soweputsometestsinyourtests.py

Created by FI$H 2000 on 2011-09-02.
Copyright (c) 2011 Objects In Space And Time, LLC. All rights reserved.
"""

import sys
import os
import unittest
import yodogg


class soweputsometestsinyourtests:
    def __init__(self):
        pass


class soweputsometestsinyourtestsTests(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_while_you_test(self):
        for ll in list(locals().values()) + list(globals().values()):
            if hasattr(ll, '__name__'):
                if ll.__name__.startswith("Processor") or ll.__name__.startswith("Spec"):
                    print "YO DOGG! %s" % ll.__name__

        


if __name__ == '__main__':
    unittest.main()