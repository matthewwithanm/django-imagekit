#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
encoding.py

From the excellent DispCalGUI by Florian Höch:

    http://dispcalgui.hoech.net/

Copyright (c) 2011 OST, LLC. 
"""
from itertools import izip, imap

def is_nan(obj):
    """
    Return boolean indicating if obj is considered not a number.
    """
    try:
        obj + 1
    except TypeError:
        return True
    return False


class OrderedDict(dict):
    
    """
    Simple ordered dictionary.
    
    Compatible with Python 3's OrderedDict, though performance is inferior 
    as the approach is different (but should be more memory efficient),
    and implements several sequence methods (__delslice__, __getslice__, 
    __setslice__, index, insert, reverse, sort).
    
    """
    
    missing = object()
    
    def __init__(self, *args, **kwargs):
        self._keys = []
        if args or kwargs:
            self.update(*args, **kwargs)
    
    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self._keys.remove(key)
    
    def __delslice__(self, i, j):
        """
        Delete a range of keys.
        """
        for key in iter(self._keys[i:j]):
            del self[key]
    
    def __eq__(self, other):
        """
        od.__eq__(y) <==> od==y.  Comparison to another OD is order-sensitive
        while comparison to a regular mapping is order-insensitive.
        """
        if isinstance(other, OrderedDict):
            return len(self) == len(other) and \
                   all(p == q for p, q in zip(self.items(), other.items()))
        return dict.__eq__(self, other)
    
    def __getslice__(self, i, j):
        """
        Get a range of keys. Return a new OrderedDict.
        """
        keys = self._keys[i:j]
        return self.__class__(zip(keys, map(self.get, keys)))
    
    def __iter__(self):
        return iter(self._keys)
    
    def __ne__(self, other):
        return not self == other
    
    def __reduce__(self):
        'Return state information for pickling'
        items = [[k, self[k]] for k in self]
        tmp = self._keys
        del self._keys
        inst_dict = vars(self).copy()
        self._keys = tmp
        if inst_dict:
            return (self.__class__, (items,), inst_dict)
        return self.__class__, (items,)
    
    def __repr__(self):
        """
        od.__repr__() <==> repr(od)
        """
        if not self:
            return "%s.%s()" % (self.__class__.__module__, self.__class__.__name__)
        return "%s.%s(%r)" % (self.__class__.__module__, self.__class__.__name__, self.items())
    
    def __reversed__(self):
        """
        od.__reversed__() -- return a reverse iterator over the keys
        """
        return reversed(self._keys)
    
    def __setitem__(self, key, value):
        if not key in self._keys:
            self._keys.append(key)
        dict.__setitem__(self, key, value)
    
    def __setslice__(self, i, j, iterable):
        """
        Set a range of keys.
        """
        for key in iter(self._keys[i:j]):
            dict.__delitem__(self, key)
        self._keys[i:j] = self.__class__(iterable).keys()
        self.update(iterable)
    
    def clear(self):
        dict.clear(self)
        del self._keys[:]
    
    def copy(self):
        return self.__class__(self)
    
    def delslice(self, key1, key2):
        """
        Like __delslice__, but takes keys instead of numerical key positions.
        """
        if key1:
            if key2:
                del self[self.index(key1):self.index(key2)]
            else:
                del self[self.index(key1):]
        elif key2:
            del self[:self.index(key2)]
        else:
            self.clear()
    
    @classmethod
    def fromkeys(cls, iterable, value=None):
        """
        Return new dict with keys from S and values equal to v.
        v defaults to None.
        """
        d = cls()
        for key in iterable:
            d[key] = value
        return d
    
    def getslice(self, key1, key2):
        """
        Like __getslice__, but takes keys instead of numerical key positions.
        """
        if key1:
            if key2:
                return self[self.index(key1):self.index(key2)]
            else:
                return self[self.index(key1):]
        elif key2:
            return self[:self.index(key2)]
        else:
            return self.copy()
    
    def index(self, key, start=0, stop=missing):
        """
        Return numerical position of key.
        Raise KeyError if the key is not present.
        """
        if start != 0 or stop is not missing:
            if stop is not missing:
                iterable = self._keys[start:stop]
            else:
                iterable = self._keys[start:]
        else:
            iterable = self._keys
        if not key in iterable:
            raise KeyError(key)
        return self._keys.index(key)
    
    def insert(self, i, key, value):
        """
        Insert key before index and assign value to self[key].
        If the key is already present, it is overwritten.
        """
        if key in self:
            del self[key]
        self._keys.insert(i, key)
        dict.__setitem__(self, key, value)
    
    def items(self):
        return zip(self._keys, self.values())
    
    def iteritems(self):
        return izip(self._keys, self.itervalues())
    
    iterkeys = __iter__
    
    def itervalues(self):
        return imap(self.get, self._keys)
    
    def key(self, value, start=0, stop=missing):
        """
        Return key of first value.
        Raise ValueError if the value is not present.
        """
        if start != 0 or stop is not missing:
            if stop is not missing:
                iterable = self[start:stop]
            else:
                iterable = self[start:]
        else:
            iterable = self
        for item in iterable.iteritems():
            if item[1] == value:
                return item[0]
        raise ValueError(value)
    
    def keys(self):
        return self._keys[:]
    
    def pop(self, key, *args):
        if key in self:
            self._keys.remove(key)
        return dict.pop(self, key, *args)
    
    def popitem(self, last=True):
        """
        od.popitem() -> (k, v), return and remove a (key, value) pair.
        Pairs are returned in LIFO order if last is true or FIFO order if false.

        """
        if last:
            key = self._keys[-1]
        else:
            key = self._keys[0]
        return key, self.pop(key)
    
    def rename(self, key, name):
        """
        Rename a key in-place.
        """
        i = self.index(key)
        value = self.pop(key)
        self.insert(i, name, value)
    
    def reverse(self):
        """
        Reverse keys in-place.
        """
        self._keys.reverse()
    
    def setdefault(self, key, value=None):
        if not key in self:
            self[key] = value
        return self[key]
    
    def setslice(self, key1, key2, iterable):
        """
        Like __setslice__, but takes keys instead of numerical key positions.
        """
        if key1:
            if key2:
                self[self.index(key1):self.index(key2)] = iterable
            else:
                self[self.index(key1):] = iterable
        elif key2:
            self[:self.index(key2)] = iterable
        else:
            self[:] = iterable
    
    def sort(self, *args, **kwargs):
        """
        Sort keys in-place.
        """
        self._keys.sort(*args, **kwargs)
    
    def update(self, *args, **kwargs):
        if len(args) > 1:
            raise TypeError("update expected at most 1 arguments, got %i" % len(args))
        for iterable in args + (kwargs, ):
            if iterable:
                if hasattr(iterable, "iteritems"):
                    self.update(iterable.iteritems())
                elif hasattr(iterable, "keys"):
                    for key in iterable.keys():
                        self[key] = iterable[key]
                else:
                    for key, val in iterable:
                        self[key] = val
    
    def values(self):
        return map(self.get, self._keys)
    
    __init__.__doc__ = dict.__init__.__doc__
    __delitem__.__doc__ = dict.__delitem__.__doc__
    __iter__.__doc__ = dict.__iter__.__doc__
    __setitem__.__doc__ = dict.__setitem__.__doc__
    clear.__doc__ = dict.clear.__doc__
    copy.__doc__ = dict.copy.__doc__
    items.__doc__ = dict.items.__doc__
    iteritems.__doc__ = dict.iteritems.__doc__
    itervalues.__doc__ = dict.itervalues.__doc__
    keys.__doc__ = dict.keys.__doc__
    pop.__doc__ = dict.pop.__doc__
    setdefault.__doc__ = dict.setdefault.__doc__
    update.__doc__ = dict.update.__doc__
    values.__doc__ = dict.values.__doc__
