#!/usr/bin/env python
# encoding: utf-8
"""
delegate.py -- AUTOMATICALLY CHAINABLE MANAGER/QUERYSET DELEGATE METHODS.

By defining manager methods, Django lets you do this:

    >>> SomeModel.objects.custom_query()

... but it WON'T let you do this:

    >>> SomeModel.objects.custom_query().another_custom_query()

unless you duplicate your methods and define a redundant queryset subclass... UNTIL NOW. 


+ With DelegateManager and @delegate, you can write maintainable custom-query logic
with free chaining. instead of defining manager methods, you define queryset methods,
decorate those you'd like to delegate, and a two-line DelegateManager subclass
specifying the queryset. ET VIOLA. Like so:


class CustomQuerySet(models.query.QuerySet):
    
    @delegate
    def qs_method(self, some_value):
        return self.filter(some_param__icontains=some_value)
    
    def dont_delegate_me(self):
        return self.filter(some_other_param="something else")

class CustomManager(DelegateManager):
    __queryset__ = CustomQuerySet

class SomeModel(models.Model):
    objects = CustomManager()


# will work:
SomeModel.objects.qs_method('yo dogg')
# will also work:
SomeModel.objects.qs_method('yo dogg').qs_method('i heard you like queryset method delegation')


+ To delegate all of the methods in a QuerySet automatically, you can create a subclass
of DelegateQuerySet. These two QuerySet subclasses work identically:


class ManualDelegator(models.query.QuerySet):
    @delegate
    def qs_method(self):
        # ...

class AutomaticDelegator(DelegateQuerySet):
    def qs_method(self):
        # ...


+ You can also apply the @delegate decorator directly to a class -- this permits you to
delegate all the methods in a class without disrupting its inheritance chain. This example
works identically to the previous two:


@delegate
class CustomQuerySet(models.query.QuerySet):
    
    def qs_method(self, some_value):
        return self.filter(some_param__icontains=some_value)



Created by Alexander Bohn on 2011-02-08.
Copyright (c) 2011 Objects in Space and Time. All rights reserved.
"""

import types
from django.db import models


def delegate(f_or_cls):
    """
    # Delegate QuerySet methods to a DelegateManager subclass by decorating them thusly:
    
    class CustomQuerySet(models.query.QuerySet):
        
        @delegate
        def qs_method(self, some_value):
            return self.filter(some_param__icontains=some_value)
        
        # ... 
    
    # You can also decorate classes -- this will delegate all of the classes' methods:
    
    @delegate
    class CustomQuerySet(models.query.QuerySet):
        
        def qs_method(self, some_value):
            return self.filter(some_param__icontains=some_value)
    
    # Both of these examples are equivalent.
    
    """
    
    if type(f_or_cls) in (types.ClassType, types.TypeType, types.ModuleType):
        # It's a class decorator.
        if hasattr(f_or_cls, '__dict__'):
            
            cls_funcs = filter(lambda attr: type(attr) == types.FunctionType, f_or_cls.__dict__.values())
            
            for cls_func in cls_funcs:
                cls_func.__delegate__ = 1
    
    else:
        # It's a function decorator.
        f_or_cls.__delegate__ = 1
    
    return f_or_cls


class DelegateSupervisor(type):
    """
    # The DelegateSupervisor metaclass handles delegation
    # of the specified methods from a QuerySet to a Manager
    # at compile-time. You don't need to invoke it to
    # perform your delegations.
    """
    def __new__(cls, name, bases, attrs):
        
        qs_delegates = dict()
        
        if '__queryset__' in attrs:
            
            qs = attrs.get('__queryset__')
            
            #if issubclass(qs, models.query.QuerySet):
            
            qs_funcs = dict(filter(lambda attr: type(attr[1]) == types.FunctionType, qs.__dict__.items()))
            
            for f_name, f in qs_funcs.items():
                if issubclass(qs, DelegateQuerySet):
                    qs_delegates[f_name] = f
                elif hasattr(f, '__delegate__'):
                    if getattr(f, '__delegate__', 1):
                        qs_delegates[f_name] = f
        
        attrs.update(qs_delegates)
        return super(DelegateSupervisor, cls).__new__(cls, name, bases, attrs)


class DelegateManager(models.Manager):
    """
    # Subclass DelegateManager and specify the queryset from which to delegate:
    
    class CustomManager(DelegateManager):
        __queryset__ = CustomQuerySet
    
    # No other methods are necessary.
    
    """
    __metaclass__ = DelegateSupervisor
    
    use_for_related_fields = True
    
    def __init__(self, fields=None, *args, **kwargs):
        super(DelegateManager, self).__init__(*args, **kwargs)
        self._fields = fields
    
    def get_query_set(self):
        if hasattr(self, '__queryset__'):
            qs = getattr(self, '__queryset__')
            return qs(self.model, self._fields)
        return None


class DelegateQuerySet(models.query.QuerySet):
    """
    # ALL methods in a DelegateQuerySet subclass will
    # be delegated -- no decoration needed.
    # These two QuerySet subclasses work identically:
    
    class ManualDelegator(models.query.QuerySet):
        @delegate
        def qs_method(self):
            # ...
    
    class AutomaticDelegator(DelegateQuerySet):
        def qs_method(self):
            # ...
    
    """
    pass



if __name__ == '__main__':
    pass