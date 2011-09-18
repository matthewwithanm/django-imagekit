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


class soyoucanprogramwhileyouprogram:
    def __init__(self):
        print "*** %s" % self.__module__


class soweputsometestsinyourtestsTests(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_while_you_test(self):
        for ll in list(locals().values()) + list(globals().values()):
            if hasattr(ll, '__name__'):
                if ll.__name__.startswith("Processor") or ll.__name__.startswith("Spec"):
                    print "YO DOGG! %s" % ll.__name__

        
class soyoucanprogramwhileyouprogramTests(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_while_you_program(self):
        whileyoutest = soyoucanprogramwhileyouprogram()
        self.assertEqual(whileyoutest.__module__, '__main__')
    
    def test_program_while_you_program(self):
        self.assertEqual(soyoucanprogramwhileyouprogram.__module__, '__main__')
    
    def test_program_while_you_test(self):
        self.assertEqual(yodogg.__package__, None)
        self.assertEqual(os.__package__, None)
        
        import numpy
        self.assertEqual(numpy.__package__, 'numpy')
    
    def test_test_while_you_program_tests(self):
        """
        THIS IS WACK. it is not equal because setup() has never been run to define the package.
        
        """
        import imagekit
        self.assertNotEqual(imagekit.__package__, 'imagekit') # MOTHERFUCKER SHOULD FAIL
        



if __name__ == '__main__':
    unittest.main()