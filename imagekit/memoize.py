#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
memoize.py

Adapted from the memoize() examples in the
decorator module documentation:

    http://pypi.python.org/pypi/decorator

Copyright (c) 2011 OST, LLC. 
"""
from decorator import decorator

def memoize(f):
    f._cache = {}
    return decorator(_memoize, f)

def _memoize(f, *args, **kw):
    if kw:
        key = args, frozenset(kw.iteritems())
    else:
        key = args
    _cache = f._cache
    if key in _cache:
        return _cache[key]
    else:
        _cache[key] = out = f(*args, **kw)
        return out
