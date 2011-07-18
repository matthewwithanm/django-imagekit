#!/usr/bin/env python
# encoding: utf-8
"""
search_indexes.py

The Haystack search Django app uses this file to define a search index.

Created by FI$H 2000 on 2011-06-17.
Copyright (c) 2011 OST, LLC. All rights reserved.
"""
import datetime
from decorator import decorator
from haystack import indexes
from imagekit import models
from imagekit.etc.profileinfo import profileinfo

@decorator
def whatever(f, *args, **kwargs):
    """
    Apparently Haystack will abort the entire index job
    for your model, with a cryptic fail message, if it
    encounters a UnicodeDecodeError.
    """
    try:
        return f(*args, **kwargs)
    except UnicodeDecodeError:
        return ''


class ICCModelIndex(indexes.RealTimeSearchIndex):
    text = indexes.CharField(document=True, use_template=False)
    
    icc = indexes.CharField(model_attr='icc')
    tags = indexes.CharField(boost=1.1)
    
    description = indexes.CharField()
    description_ngram = indexes.EdgeNgramField()
    
    colorspace = indexes.CharField()
    pcs = indexes.CharField()
    
    '''
    w = indexes.MultiValueField()
    r = indexes.MultiValueField()
    g = indexes.MultiValueField()
    b = indexes.MultiValueField()
    '''
    
    profileclass = indexes.CharField()
    technology = indexes.CharField()
    illuminant_measured = indexes.CharField()
    intent = indexes.CharField()
    viewconditions = indexes.CharField()
    datetime = indexes.DateTimeField(default=datetime.date.today)
    
    creator = indexes.CharField()
    devicemodel = indexes.CharField()
    manufacturer = indexes.CharField()
    copyright = indexes.CharField()
    
    def get_model(self):
        return models.ICCModel
    
    def index_queryset(self):
        return self.get_model().objects.all()
    
    @whatever
    def prepare_icc(self, obj):
        if obj.icc:
            return profileinfo(obj.icc, barf=False)
        return ''
        
    @whatever
    def prepare_tags(self, obj):
        if obj.icc:
            return " ".join(obj.icc.tags.keys())
        return ''
    
    @whatever
    def prepare_description(self, obj):
        if obj.icc:
            return obj.icc.getDescription()
        return ''
    
    @whatever
    def prepare_colorspace(self, obj):
        if obj.icc:
            return obj.icc.colorSpace
        return ''
    
    @whatever
    def prepare_pcs(self, obj):
        if obj.icc:
            return obj.icc.connectionColorSpace
        return ''
    
    '''
    @whatever
    def prepare_w(self, obj):
        if obj.icc:
            if obj.icc.tags.get('wtpt'):
                return obj.icc.tags.wtpt.values()
        return []
    
    @whatever
    def prepare_r(self, obj):
        if obj.icc:
            if obj.icc.tags.get('rXYZ'):
                return obj.icc.tags.rXYZ.values()
        return []
    
    @whatever
    def prepare_g(self, obj):
        if obj.icc:
            if obj.icc.tags.get('gXYZ'):
                return obj.icc.tags.gXYZ.values()
        return []
    
    @whatever
    def prepare_b(self, obj):
        if obj.icc:
            if obj.icc.tags.get('bXYZ'):
                return obj.icc.tags.bXYZ.values()
        return []
    '''
    
    @whatever
    def prepare_profileclass(self, obj):
        if obj.icc:
            return obj.icc.getProfileClass()
        return ''
    
    @whatever
    def prepare_technology(self, obj):
        if obj.icc:
            return obj.icc.getTechnologySummary()
        return ''
    
    @whatever
    def prepare_illuminant_measured(self, obj):
        if obj.icc:
            return obj.icc.getMeasuredIlluminant()
        return ''
    
    @whatever
    def prepare_intent(self, obj):
        if obj.icc:
            return obj.icc.getRenderingIntent()
        return ''
    
    @whatever
    def prepare_viewconditions(self, obj):
        if obj.icc:
            return obj.icc.getViewingConditionsDescription()
        return ''
    
    @whatever
    def prepare_datetime(self, obj):
        if obj.icc:
            try:
                return datetime.datetime(*obj.icc.dateTime)
            except ValueError:
                pass
        return datetime.datetime.now()
    
    @whatever
    def prepare_creator(self, obj):
        if obj.icc:
            return obj.icc.creator
        return ''
    
    @whatever
    def prepare_devicemodel(self, obj):
        if obj.icc:
            return obj.icc.getDeviceModelDescription()
        return ''
    
    @whatever
    def prepare_manufacturer(self, obj):
        if obj.icc:
            return obj.icc.getDeviceManufacturerDescription()
        return ''
    
    @whatever
    def prepare_copyright(self, obj):
        if obj.icc:
            return obj.icc.getCopyright()
        return ''
    
    def _everything(self, obj):
        
        out = ""
        
        try:
            out += "" + \
                self.prepare_icc(obj) + " " + \
                self.prepare_tags(obj) + " " + \
                self.prepare_description(obj) + " " + \
                self.prepare_colorspace(obj) + " " + \
                self.prepare_pcs(obj) + " " + \
                self.prepare_profileclass(obj) + " " + \
                self.prepare_technology(obj) + " " + \
                self.prepare_illuminant_measured(obj) + " " + \
                self.prepare_intent(obj) + " " + \
                self.prepare_viewconditions(obj) + " " + \
                self.prepare_creator(obj) + " " + \
                self.prepare_devicemodel(obj) + " " + \
                self.prepare_manufacturer(obj) + " " + \
                self.prepare_copyright(obj) + " "
        
        except UnicodeDecodeError:
            pass
        
        return out
    
    @whatever
    def prepare_description_ngram(self, obj):
        if obj.icc:
            return self._everything(obj)
        return ''
    
    @whatever
    def prepare(self, obj):
        if not hasattr(self, 'cnt'):
            self.cnt = 1
        else:
            self.cnt += 1
        
        #print "%3d \t Preparing %s (%s)..." % (self.cnt, obj, obj.pk)
        self.prepared_data = super(ICCModelIndex, self).prepare(obj)
        self.prepared_data['text'] = self._everything(obj)
        return self.prepared_data
