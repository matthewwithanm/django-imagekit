#!/usr/bin/env python
# encoding: utf-8
"""
neuquant.py

Created by FI$H 2000 on 2011-06-14.
Copyright (c) 2011 OST, LLC.
"""

import os
from django.core.management import setup_environ
import settings
setup_environ(settings)
from imagekit.utils import logg

try:
    import PIL
    from PIL import Image, ImageChops
    from PIL.GifImagePlugin import getheader, getdata
except ImportError:
    PIL = None

try:
    import numpy as np
except ImportError:
    np = None

try:
    from scipy.spatial import cKDTree
except ImportError:
    cKDTree = None


class NeuQuant:
    """ NeuQuant(image, samplefac=10, colors=256)
    
    samplefac should be an integer number of 1 or higher, 1 
    being the highest quality, but the slowest performance. 
    With avalue of 10, one tenth of all pixels are used during 
    training. This value seems a nice tradeof between speed
    and quality.
    
    colors is the amount of colors to reduce the image to. This
    should best be a power of two.
    
    See also:
    http://members.ozemail.com.au/~dekker/NEUQUANT.HTML
    
    License of the NeuQuant Neural-Net Quantization Algorithm
    ---------------------------------------------------------
    
    Copyright (c) 1994 Anthony Dekker
    Ported to python by Marius van Voorden in 2010
    Subsequently copied and pasted by Alexander Bohn in 2011
    Most comments are presumably by Mr. van Voorden.
    
    NEUQUANT Neural-Net quantization algorithm by Anthony Dekker, 1994.
    See "Kohonen neural networks for optimal colour quantization"
    in "network: Computation in Neural Systems" Vol. 5 (1994) pp 351-367.
    for a discussion of the algorithm.
    See also  http://members.ozemail.com.au/~dekker/NEUQUANT.HTML
    
    Any party obtaining a copy of these files from the author, directly or
    indirectly, is granted, free of charge, a full and unrestricted irrevocable,
    world-wide, paid up, royalty-free, nonexclusive right and license to deal
    in this software and documentation files (the "Software"), including without
    limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons who receive
    copies from any such party to do so, with the only requirement being
    that this copyright notice remain intact.
    
    """
    
    NCYCLES = None # Number of learning cycles
    NETSIZE = None # Number of colours used
    SPECIALS = None # Number of reserved colours used
    BGCOLOR = None # Reserved background colour
    CUTNETSIZE = None
    MAXNETPOS = None
    INITRAD = None # For 256 colours, radius starts at 32
    RADIUSBIASSHIFT = None
    RADIUSBIAS = None
    INITBIASRADIUS = None
    RADIUSDEC = None # Factor of 1/30 each cycle
    ALPHABIASSHIFT = None
    INITALPHA = None # biased by 10 bits
    GAMMA = None
    BETA = None
    BETAGAMMA = None
    
    network = None # The network itself
    colormap = None # The network itself
    netindex = None # For network lookup - really 256
    bias = None # Bias and freq arrays for learning
    freq = None
    pimage = None
    
    # Four primes near 500 - assume no image has a length so large
    # that it is divisible by all four primes
    PRIME1 = 499
    PRIME2 = 491
    PRIME3 = 487
    PRIME4 = 503
    MAXPRIME = PRIME4
    
    pixels = None
    samplefac = None
    a_s = None
    
    def setconstants(self, samplefac, colors):
        self.NCYCLES = 100 # Number of learning cycles
        self.NETSIZE = colors # Number of colours used
        self.SPECIALS = 3 # Number of reserved colours used
        self.BGCOLOR = self.SPECIALS - 1 # Reserved background colour
        self.CUTNETSIZE = self.NETSIZE - self.SPECIALS
        self.MAXNETPOS = self.NETSIZE - 1
        
        self.INITRAD = self.NETSIZE / 8 # For 256 colours, radius starts at 32
        self.RADIUSBIASSHIFT = 6
        self.RADIUSBIAS = 1 << self.RADIUSBIASSHIFT
        self.INITBIASRADIUS = self.INITRAD * self.RADIUSBIAS
        self.RADIUSDEC = 30 # Factor of 1/30 each cycle
        
        self.ALPHABIASSHIFT = 10 # Alpha starts at 1
        self.INITALPHA = 1 << self.ALPHABIASSHIFT # biased by 10 bits
        
        self.GAMMA = 1024.0
        self.BETA = 1.0 / 1024.0
        self.BETAGAMMA = self.BETA * self.GAMMA
        
        self.network = np.empty((self.NETSIZE, 3), dtype='float64') # The network itself
        self.colormap = np.empty((self.NETSIZE, 4), dtype='int32') # The network itself
        
        self.netindex = np.empty(256, dtype='int32') # For network lookup - really 256
        
        self.bias = np.empty(self.NETSIZE, dtype='float64') # Bias and freq arrays for learning
        self.freq = np.empty(self.NETSIZE, dtype='float64')
        
        self.pixels = None
        self.samplefac = samplefac
        
        self.a_s = {}
    
    def __init__(self, image, samplefac=10, colors=256):
        
        if np is None: # Check Numpy
            raise RuntimeError("Need Numpy for the NeuQuant algorithm.")
        
        if image.size[0] * image.size[1] < NeuQuant.MAXPRIME: # Check image
            raise IOError("Image is too small")
        assert image.mode == "RGBA"
        
        # Initialize
        self.setconstants(samplefac, colors)
        self.pixels = np.fromstring(image.tostring(), np.uint32)
        self.setUpArrays()
        self.learn()
        self.fix()
        self.inxbuild()
    
    def writeColourMap(self, rgb, outstream):
        for i in range(self.NETSIZE):
            bb = self.colormap[i,0];
            gg = self.colormap[i,1];
            rr = self.colormap[i,2];
            out.write(rr if rgb else bb)
            out.write(gg)
            out.write(bb if rgb else rr)
        return self.NETSIZE
    
    def setUpArrays(self):
        self.network[0,0] = 0.0    # Black
        self.network[0,1] = 0.0
        self.network[0,2] = 0.0
        
        self.network[1,0] = 255.0    # White
        self.network[1,1] = 255.0
        self.network[1,2] = 255.0
        # RESERVED self.BGCOLOR # Background
        
        for i in range(self.SPECIALS):
            self.freq[i] = 1.0 / self.NETSIZE
            self.bias[i] = 0.0
        
        for i in range(self.SPECIALS, self.NETSIZE):
            p = self.network[i]
            p[:] = (255.0 * (i - self.SPECIALS)) / self.CUTNETSIZE
            
            self.freq[i] = 1.0 / self.NETSIZE
            self.bias[i] = 0.0
    
    ''' Omitted: setPixels '''
    
    def altersingle(self, alpha, i, b, g, r):
        """Move neuron i towards biased (b,g,r) by factor alpha"""
        n = self.network[i] # Alter hit neuron
        n[0] -= (alpha * (n[0] - b))
        n[1] -= (alpha * (n[1] - g))
        n[2] -= (alpha * (n[2] - r))
    
    def geta(self, alpha, rad):
        try:
            return self.a_s[(alpha, rad)]
        except KeyError:
            length = rad * 2 - 1
            mid = length / 2
            q = np.array(range(mid - 1, -1, -1)+range(-1, mid))
            a = alpha * (rad * rad - q * q) / (rad * rad)
            a[mid] = 0
            self.a_s[(alpha, rad)] = a
            return a
    
    def alterneigh(self, alpha, rad, i, b, g, r):
        if i - rad >= self.SPECIALS - 1:
            lo = i - rad
            start = 0
        else:
            lo = self.SPECIALS - 1
            start = (self.SPECIALS - 1 - (i - rad))
            
        if i+rad <= self.NETSIZE:
            hi = i + rad
            end = rad * 2 - 1
        else:
            hi = self.NETSIZE
            end = (self.NETSIZE - (i+rad))
        
        a = self.geta(alpha, rad)[start:end]
        
        p = self.network[lo+1:hi]
        p -= np.transpose(np.transpose(p - np.array([b, g, r])) * a)
    
    def contest(self, b, g, r):
        """ Search for biased BGR values
                Finds closest neuron (min dist) and updates self.freq
                finds best neuron (min dist-self.bias) and returns position
                for frequently chosen neurons, self.freq[i] is high and self.bias[i] is negative
                self.bias[i] = self.GAMMA*((1/self.NETSIZE)-self.freq[i])"""
        i, j = self.SPECIALS, self.NETSIZE
        dists = abs(self.network[i:j] - np.array([b,g,r])).sum(1)
        bestpos = i + np.argmin(dists)
        biasdists = dists - self.bias[i:j]
        bestbiaspos = i + np.argmin(biasdists)
        self.freq[i:j] *= (1-self.BETA)
        self.bias[i:j] += self.BETAGAMMA * self.freq[i:j]
        self.freq[bestpos] += self.BETA
        self.bias[bestpos] -= self.BETAGAMMA
        return bestbiaspos
    
    def specialFind(self, b, g, r):
        for i in range(self.SPECIALS):
            n = self.network[i]
            if n[0] == b and n[1] == g and n[2] == r:
                return i
        return -1
    
    def learn(self):
        biasRadius = self.INITBIASRADIUS
        alphadec = 30 + ((self.samplefac - 1) / 3)
        lengthcount = self.pixels.size
        samplepixels = lengthcount / self.samplefac
        delta = samplepixels / self.NCYCLES
        alpha = self.INITALPHA
        
        i = 0;
        rad = biasRadius >> self.RADIUSBIASSHIFT
        if rad <= 1:
            rad = 0
        
        logg.info("Beginning 1D learning: samplepixels = " + str(samplepixels) + ", rad = " + str(rad))
        
        step = 0
        pos = 0
        if lengthcount % NeuQuant.PRIME1 != 0:
            step = NeuQuant.PRIME1
        elif lengthcount % NeuQuant.PRIME2 != 0:
            step = NeuQuant.PRIME2
        elif lengthcount % NeuQuant.PRIME3 != 0:
            step = NeuQuant.PRIME3
        else:
            step = NeuQuant.PRIME4
        
        i = 0
        printed_string = ''
        
        while i < samplepixels:
            
            if i % 100 == 99:
                tmp = '\b' * len(printed_string)
                printed_string = str((i + 1) * 100 / samplepixels) + "%\n"
                
                #print tmp + printed_string,
            
            p = self.pixels[pos]
            r = (p >> 16) & 0xff
            g = (p >>  8) & 0xff
            b = (p      ) & 0xff
            
            if i == 0: # Remember background colour
                self.network[self.BGCOLOR] = [b, g, r]
            
            j = self.specialFind(b, g, r)
            if j < 0:
                j = self.contest(b, g, r)
            
            if j >= self.SPECIALS: # Don't learn for specials
                a = (1.0 * alpha) / self.INITALPHA
                self.altersingle(a, j, b, g, r)
                if rad > 0:
                    self.alterneigh(a, rad, j, b, g, r)
            
            pos = (pos + step) % lengthcount
            
            i += 1
            if i % delta == 0:
                alpha -= alpha / alphadec
                biasRadius -= biasRadius / self.RADIUSDEC
                rad = biasRadius >> self.RADIUSBIASSHIFT
                if rad <= 1:
                    rad = 0
        
        logg.info("Finished 1D learning: final alpha = %s !" % ((1.0 * alpha) / self.INITALPHA))
    
    def fix(self):
        for i in range(self.NETSIZE):
            for j in range(3):
                x = int(0.5 + self.network[i,j])
                x = max(0, x)
                x = min(255, x)
                self.colormap[i,j] = x
            self.colormap[i,3] = i
    
    def inxbuild(self):
        previouscol = 0
        startpos = 0
        for i in range(self.NETSIZE):
            p = self.colormap[i]
            q = None
            smallpos = i
            smallval = p[1] # Index on g
            # Find smallest in i..self.NETSIZE-1
            for j in range(i + 1, self.NETSIZE):
                q = self.colormap[j]
                if q[1] < smallval: # Index on g
                    smallpos = j
                    smallval = q[1] # Index on g
            
            q = self.colormap[smallpos]
            # Swap p (i) and q (smallpos) entries
            if i != smallpos:
                p[:], q[:] = q, p.copy()
            
            # smallval entry is now in position i
            if smallval != previouscol:
                self.netindex[previouscol] = (startpos + i) >> 1
                for j in range(previouscol + 1, smallval):
                    self.netindex[j] = i
                previouscol = smallval
                startpos = i
        self.netindex[previouscol] = (startpos+self.MAXNETPOS) >> 1
        for j in range(previouscol + 1, 256): # Really 256
            self.netindex[j] = self.MAXNETPOS
    
    def paletteImage(self):
        """ PIL weird interface for making a paletted image: create an image which
            already has the palette, and use that in Image.quantize. This function
            returns this palette image. """
        if self.pimage is None:
            palette = []
            for i in range(self.NETSIZE):
                palette.extend(self.colormap[i][:3])
                
            palette.extend([0] * (256-self.NETSIZE) * 3)
            
            # a palette image to use for quant
            self.pimage = Image.new("P", (1, 1), 0)
            self.pimage.putpalette(palette)
        return self.pimage
    
    def quantize(self, image):
        """ Use a kdtree to quickly find the closest palette colors for the pixels """
        if cKDTree:
            return self.quantize_with_scipy(image)
        else:
            logg.warning('Scipy not available, falling back to slower version.')
            return self.quantize_without_scipy(image)
    
    def quantize_with_scipy(self, image):
        w, h = image.size
        px = np.asarray(image).copy()
        px2 = px[:,:,:3].reshape((w * h,3))
        
        kdtree = cKDTree(self.colormap[:,:3], leafsize=10)
        result = kdtree.query(px2)
        colorindex = result[1]
        
        logg.info("Distance: %s" % (result[0].sum() / (w * h)))
        
        px2[:] = self.colormap[colorindex,:3]
        return Image.fromarray(px).convert("RGB").quantize(palette=self.paletteImage())
    
    def quantize_without_scipy(self, image):
        """" This function can be used if no scipy is availabe.
        It's 7 times slower though.
        """
        w,h = image.size
        px = np.asarray(image).copy()
        memo = {}
        for j in range(w):
            for i in range(h):
                key = (px[i,j,0], px[i,j,1], px[i,j,2])
                try:
                    val = memo[key]
                except KeyError:
                    val = self.convert(key)
                    memo[key] = val
                px[i,j,0], px[i,j,1], px[i,j,2] = val
        return Image.fromarray(px).convert("RGB").quantize(palette=self.paletteImage())
    
    def convert(self, (r, g, b)):
        i = self.inxsearch(r, g, b)
        return self.colormap[i,:3]
    
    def inxsearch(self, r, g, b):
        """Search for BGR values 0..255 and return colour index"""
        dists = (self.colormap[:,:3] - np.array([r,g,b]))
        a = np.argmin((dists * dists).sum(1))
        return a

if __name__ == "__main__":
    from django.core.management import setup_environ
    import settings
    setup_environ(settings)
    from jogging import logging as logg
    import urllib2, StringIO, random
    
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
    
    print "NeuQuantizing with samplefac=10..."
    quant = NeuQuant(img.convert("RGBA").resize((64, 64), Image.NEAREST), 10)
    
    if np:
        out = np.array(quant.colormap).reshape(16, 16, 4)
        #out.T[0:3].T
        
        print out
        
        outimg = Image.new('RGBA', (256, 1), (0,0,0))
        outimg.putdata([tuple(t[0]) for t in out.T[0:3].T.reshape(256, 1, 3).tolist()])
        a = outimg.resize((512, 256), Image.NEAREST)
        a.show()
    
    else:
        logg.info("**** QUANT! %s" % quant)
    


