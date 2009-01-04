""" Base imagekit specification classes

This module holds the base implementations and defaults for imagekit
specification classes. Users import and subclass these classes to define new
specifications. 

"""
class Spec(object):
    increment_count = False
    pre_cache = False
    jpeg_quality = 70
    processors = []
