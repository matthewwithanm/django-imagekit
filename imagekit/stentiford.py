#!/usr/bin/env python
# encoding: utf-8
"""
stentiford.py

Python implementation of the Stentiford image attention model:

    http://www.ee.ucl.ac.uk/~fstentif/PCS2001.pdf

Adapted from the Java implementation of same from the excellent Lire image search engine,
originally by Mathias Lux of SemanticMetadata.net. For details, see:

    http://bit.ly/mbcnoa
    http://www.semanticmetadata.net/2010/03/22/visual-attention-in-lire/

Created by FI$H 2000 on 2011-06-29.
Copyright (c) 2011 OST, LLC. All rights reserved.

"""
import sys, os, numpy, random
from PIL import Image
from colorsys import rgb_to_hsv

class StentifordModel(object):
    
    neighborhood_size = 3
    random_neighborhood = set(xrange(neighborhood_size))
    max_checks = 100
    max_dist = 40
    radius = 2
    
    side = 0
    cnt = 0
    
    dt = numpy.int32
    
    def __init__(self, *args, **kwargs):
        """
        Class encapsulating the Stentiford image attention algorithm.
        
        Use it thusly:
        
            sten = StentifordModel(max_checks=50) # optional args override defaults
            sten.ogle(pilimage)
            attention_image_pil_instance = sten.pilimage
        
        A small demo script is included -- run this file directly to execute it.
        
        The default parameter values and the implementation structure are
        a more-or-less literal translation from the Lire implementation. As such,
        these values are most likely suboptimal. Interested parties are encouraged
        to peruse the Lire source, via the bit.ly link in the header.
        
        WARNING: right now this is incredibly slow -- analyzing an image larger than
        a thumbnail will criminally abuse your processor for a few minutes, with the
        default settings;unless you have a stack of amazon cluster AMIs you're not
        using it's not going to play nice with synchronous web request invocations.
        
        """
        self.neighborhood_size = kwargs.pop('neighborhood_size', self.neighborhood_size)
        self.max_checks = kwargs.pop('max_checks', self.max_checks)
        self.max_dist = kwargs.pop('max_dist', self.max_dist)
        
        super(StentifordModel, self).__init__(*args, **kwargs)
        random.seed()
        
        # compute possible neighbors with our params
        self.side = 2*self.radius+1
        self.cnt = 0
        
        from_the_block = list()
        for i in xrange(self.radius*-1, self.radius+1):
            for j in xrange(self.radius*-1, self.radius+1):
                if j > 0 or i > 0:
                    from_the_block.append((i, j))
                    self.cnt += 0
        
        self.possible_neighbors = numpy.array(from_the_block, dtype=self.dt)
    
    def ogle(self, pilimage):
        """
        In my experience, this algorithm has a particular affinity for images of ladies,
        hence the method name.
        
        """
        match = True
        
        # initialize attention model matrix with the dimensions of our image,
        # loaded with zeroes:
        self.attention_model = numpy.array(
            [0] * len(pilimage.getdata()),
            dtype=self.dt,
        ).reshape(*pilimage.size)
        
        # populate the matrix with per-pixel attention values
        for x in xrange(self.radius, pilimage.size[0]-self.radius):
            for y in xrange(self.radius, pilimage.size[1]-self.radius):
                self.regentrify()
                
                xmatrix = self.there_goes_the_neighborhood(x, y, pilimage)
                
                for checks in xrange(self.max_checks):
                    ymatrix = self.there_goes_the_neighborhood(
                        random.randint(
                            0, (pilimage.size[0]-2*self.radius)+self.radius,
                        ),
                        random.randint(
                            0, (pilimage.size[1]-2*self.radius)+self.radius,
                        ),
                        pilimage,
                    )
                    
                    match = True
                    for idx in xrange(xmatrix.shape[0]):
                        if self.distance(xmatrix[idx], ymatrix[idx]) > self.max_dist:
                            match = False
                            break
                    
                    if not match:
                        self.attention_model[x, y] += 1
    
    def distance(self, a0, a1):
        """
        Get the L1 distance between two arrays.
        Implementation cribbed from Spectral Python -- http://spectralpython.sourceforge.net/
        
        """
        return numpy.sum(abs((a0 - a1)))
    
    def there_goes_the_neighborhood(self, x, y, pilimage):
        """
        Retrieve a neighborhood of values around a given pixel in the source image.
        
        """
        out = list()
        for denizen in self.random_neighborhood:
            
            '''
            print "GETPIXEL: %s, %s" % (
                (x + self.possible_neighbors[denizen, 0]),
                (y + self.possible_neighbors[denizen, 1]),
            )
            '''
            
            i_want_x = abs(int(x + self.possible_neighbors[denizen, 0]))
            i_want_y = abs(int(y + self.possible_neighbors[denizen, 1]))
            
            pix = pilimage.getpixel((
                i_want_x < pilimage.size[0] and i_want_x or pilimage.size[0]-1,
                i_want_y < pilimage.size[1] and i_want_y or pilimage.size[1]-1,
            ))
            out.append(rgb_to_hsv(*pix))
        
        return numpy.array(out, dtype=self.dt)
    
    def regentrify(self):
        """
        Repopulate the random neighborhood array with random values,
        bounded by the size of possible_neighbors (which itself is
        derived from the algo's initial parameter values.)
        
        """
        self.random_neighborhood.clear()
        denizen = random.randint(0, self.possible_neighbors.shape[0])
        
        if denizen == self.possible_neighbors.shape[0]:
            denizen -= 1
        
        self.random_neighborhood.add(denizen)
    
    @property
    def pilimage(self):
        """
        PIL image instance property containing the visualized analysis results.
        
        """
        if hasattr(self, 'attention_model'):
            pilout = Image.new('RGB', self.attention_model.shape)
            for i in xrange(self.attention_model.shape[0]):
                for j in xrange(self.attention_model.shape[1]):
                    pix = self.attention_model[i, j]
                    compand = int((float(pix) / float(self.max_checks)) * 255.0)
                    pilout.putpixel((i, j), (compand, compand, compand))
            return pilout
        return None


if __name__ == '__main__':
    from django.core.management import setup_environ
    import settings
    setup_environ(settings)
    
    import urllib2, StringIO, random
    from imagekit.utils import logg
    
    urls = [
        'http://ost2.s3.amazonaws.com/images/_uploads/IfThen_Detail_Computron_Orange_2to3_010.jpg',
        'http://ost2.s3.amazonaws.com/images/_uploads/2805163544_1321ee6d30_o.jpg',
        'http://ost2.s3.amazonaws.com/images/_uploads/IfThen_Detail_Computron_Silver_2to3_010.jpg',
        'http://ost2.s3.amazonaws.com/images/_uploads/Josef_Muller_Brockmann_Detail_Lights_2to3_000.jpg',
        'http://ost2.s3.amazonaws.com/images/_uploads/P4141870.jpg',
        'http://ost2.s3.amazonaws.com/images/_uploads/After_The_Quake_Detail_Text_2to3_000.jpg',
        'http://ost2.s3.amazonaws.com/images/_uploads/P4141477.jpg',
        'http://ost2.s3.amazonaws.com/images/_uploads/P4141469.jpg',
        'http://ost2.s3.amazonaws.com/images/_uploads/IMG_1310.jpg',
        'http://ost2.s3.amazonaws.com/images/_uploads/P4141472.jpg',
    ]
    
    random.seed()
    imgurl = random.choice(urls)
    
    print "Loading image: %s" % imgurl
    imgstr = urllib2.urlopen(imgurl).read()
    img = Image.open(StringIO.StringIO(imgstr))
    img.show()
    
    img = img.resize((150, 150), Image.NEAREST)
    
    print "Stentifording..."
    stenty = StentifordModel(max_checks=55)
    stenty.ogle(img)
    stenty.pilimage.show()
    
    print "Stentiforded!"
    
