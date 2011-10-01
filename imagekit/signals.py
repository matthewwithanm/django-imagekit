#!/usr/bin/env python
# encoding: utf-8
"""
signals.py

Custom asynchronous signals used by ImageKit.

AsyncSignal is a part of dango-signalqueue, which provides
queue and worker processes that make them work:

    https://github.com/fish2000/django-signalqueue

The precursors of django-signalqueue app were originally
written as a part of ImageKit, to allow ImageModels laden
with processor-laden ImageSpec definitions to be saved
and edited without beachballing the client and melting
the webserver.

Created by FI$H 2000 on 2011-10-01.
Copyright (c) 2011 Objects In Space And Time, LLC. All rights reserved.


"""
from signalqueue import mappings
from signalqueue.dispatcher import AsyncSignal


pre_cache = AsyncSignal(providing_args={
    'instance':             mappings.ModelInstanceMap,
})


clear_cache = AsyncSignal(providing_args={
    'instance':             mappings.ModelInstanceMap,
})

prepare_spec = AsyncSignal(providing_args={
    'instance':             mappings.ModelInstanceMap,
    'spec_name':            mappings.IDMap,
})

delete_spec = AsyncSignal(providing_args={
    'instance':             mappings.ModelInstanceMap, 
    'spec_name':            mappings.IDMap,
})

refresh_hash = AsyncSignal(providing_args={
    'instance':             mappings.ModelInstanceMap,
})


refresh_color = AsyncSignal(providing_args={
    'instance':             mappings.ModelInstanceMap,
})


refresh_icc_data = AsyncSignal(providing_args={
    'instance':             mappings.ModelInstanceMap,
})


refresh_exif_data = AsyncSignal(providing_args={
    'instance':             mappings.ModelInstanceMap,
})


save_related_histogram = AsyncSignal(providing_args={
    'instance':             mappings.ModelInstanceMap,
})

refresh_histogram_channel = AsyncSignal(providing_args={
    'instance':             mappings.ModelInstanceMap, 
    'channel_name':         mappings.IDMap,
})
