#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
profileinfo.py

Dump info from the ICC profile python structure defined in ICCProfile.py.
This and that weree both originally by Florian Höch, from dispcalGUI:

    http://dispcalgui.hoech.net/

Copyright (c) 2011 OST, LLC. 
"""

from time import strftime
import os, sys, binascii
from imagekit.etc import spectralarithmetic

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                ".."))

from imagekit.ICCProfile import ICCProfile, XYZType


def prettyprint(iterable, level=1):
    def pp(iterable, level=1):
        for key, value in iterable.iteritems():
            if hasattr(value, "iteritems"):
                prettyprint.out += u"%s%s\n" % (" " * 4 * level, "%s:" % key.capitalize())
                pp(value, level + 1)
            else:
                prettyprint.out += u"%s%s%s\n" % (" " * 4 * level, "%s:" % key.capitalize(), str(value))
        return prettyprint.out
    prettyprint.out = ""
    return pp(iterable, level)


def profileinfo(profile, barf=True):
    if not isinstance(profile, ICCProfile):
        profile = ICCProfile(profile)
    # Attributes
    out = ""
    out += u"%s%s%s\n" % ("Size:", profile.size, "Bytes (%.1f KB)" % (profile.size / 1024.0))
    out += u"%s%s\n" % ("Preferred CMM:", profile.preferredCMM)
    out += u"%s%s\n" % ("ICC version:", profile.version)
    out += u"%s%s\n" % ("Class:", profile.profileClass)
    out += u"%s%s\n" % ("Colorspace:", profile.colorSpace)
    out += u"%s%s\n" % ("PCS:", profile.connectionColorSpace)
    out += u"%s%s\n" % ("Date/Time:", strftime("%Y-%m-%d %H:%M:%S",
                                 profile.dateTime + (0, 0, -1)))
    out += u"%s%s\n" % ("Platform:", profile.platform)
    out += u"%s%s\n" % ("Embedded:", profile.embedded)
    out += u"%s%s\n" % ("Independent:", profile.independent)
    out += u"%s\n" % ("Device:",)
    for key in ("manufacturer", "model"):
        profile.device[key] = binascii.hexlify(profile.device[key]).upper()
    out += u"%s\n" % (prettyprint(profile.device),)
    out += u"%s%s\n" % ("Rendering Intent:", profile.intent)
    out += u"%s%s\n" % ("Illuminant:", " ".join(str(n * 100) for n in profile.illuminant.values()))
    out += u"%s%s\n" % ("Creator:", profile.creator.decode('UTF-8', 'replace'))
    out += u"%s%s\n" % ("ID:", binascii.hexlify(profile.ID).upper())
    # Tags
    out += u"%s%s\n" % ("Description:", profile.getDescription().decode('UTF-8', 'replace'))
    out += u"%s%s\n" % ("Copyright:", profile.getCopyright())
    if "dmnd" in profile.tags:
        out += u"%s\n" % ("Device Manufacturer Description:",)
        out += u"%s\n" % (profile.getDeviceManufacturerDescription(),)
    if "dmdd" in profile.tags:
        out += u"%s%s\n" % ("Device Model Description:", profile.getDeviceModelDescription())
    if "vued" in profile.tags:
        out += u"%s\n" % ("Viewing Conditions Description:",)
        out += u"%s\n" % (profile.getViewingConditionsDescription(),)
    wtpt_profile_norm = tuple(n * 100 for n in profile.tags.wtpt.values())
    if "chad" in profile.tags:
        # undo chromatic adaption of profile whitepoint
        X, Y, Z = wtpt_profile_norm
        M = spectralarithmetic.Matrix3x3(profile.tags.chad).inverted()
        XR = X * M[0][0] + Y * M[0][1] + Z * M[0][2]
        YR = X * M[1][0] + Y * M[1][1] + Z * M[1][2]
        ZR = X * M[2][0] + Y * M[2][1] + Z * M[2][2]
        wtpt_profile_norm = tuple((n / YR) * 100.0 for n in (XR, YR, ZR))
    if "lumi" in profile.tags and isinstance(profile.tags.lumi, XYZType):
        out += u"%s%s\n" % ("Luminance:", profile.tags.lumi.Y)
    out += u"%s%s\n" % ("Actual Whitepoint XYZ:", " ".join(str(n) for n in wtpt_profile_norm))
    out += u"%s%s\n" % ("Correlated Color Temperature:", spectralarithmetic.XYZ2CCT(*wtpt_profile_norm))
    if barf:
        print out
    return out

if __name__ == "__main__":
    for arg in sys.argv[1:]:
        profileinfo(arg)
