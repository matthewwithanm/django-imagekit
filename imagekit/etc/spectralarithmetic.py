#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
spectralarithmetic.py 

Renamed from 'colormath' for inclusion in ImageKit as it conflicts another such-named
library with a similar bent. This and that weree both originally by Florian Höch,
from dispcalGUI:

    http://dispcalgui.hoech.net/

Copyright (c) 2011 OST, LLC. 
"""

import math, numpy

CIEilluminants = {
	# en.wikipedia.org/wiki/Standard_illuminant
	#
	# name  white point                          CCT      Remark
	#       CIE 1931 (2°)      CIE 1964 (10°)
	#       x         y        x        y
	"A":    [0.44757, 0.40745, 0.45117, 0.40594, 2856], # Incandescent / Tungsten
	"B":    [0.34842, 0.35161, 0.3498,  0.3527,  4874], # {obsolete} Direct sunlight at noon
	"C":    [0.31006, 0.31616, 0.31039, 0.31905, 6774], # {obsolete} Average / North sky Daylight
	"D50":  [0.34567, 0.35850, 0.34773, 0.35952, 5003], # Horizon Light. ICC profile PCS
	"D55":  [0.33242, 0.34743, 0.33411, 0.34877, 5503], # Mid-morning / Mid-afternoon Daylight
	"D65":  [0.31271, 0.32902, 0.31382, 0.33100, 6504], # Noon Daylight: Television, sRGB color space
	"D75":  [0.29902, 0.31485, 0.29968, 0.31740, 7504], # North sky Daylight
	"E":    [1.0 / 3, 1.0 / 3, 1.0 / 3, 1.0 / 3, 5454], # Equal energy
	"F1":   [0.31310, 0.33727, 0.31811, 0.33559, 6430], # Daylight Fluorescent
	"F2":   [0.37208, 0.37529, 0.37925, 0.36733, 4230], # Cool White Fluorescent
	"F3":   [0.40910, 0.39430, 0.41761, 0.38324, 3450], # White Fluorescent
	"F4":   [0.44018, 0.40329, 0.44920, 0.39074, 2940], # Warm White Fluorescent
	"F5":   [0.31379, 0.34531, 0.31975, 0.34246, 6350], # Daylight Fluorescent
	"F6":   [0.37790, 0.38835, 0.38660, 0.37847, 4150], # Lite White Fluorescent
	"F7":   [0.31292, 0.32933, 0.31569, 0.32960, 6500], # D65 simulator, Daylight simulator
	"F8":   [0.34588, 0.35875, 0.34902, 0.35939, 5000], # D50 simulator, Sylvania F40 Design 50
	"F9":   [0.37417, 0.37281, 0.37829, 0.37045, 4150], # Cool White Deluxe Fluorescent
	"F10":  [0.34609, 0.35986, 0.35090, 0.35444, 5000], # Philips TL85, Ultralume 50
	"F11":  [0.38052, 0.37713, 0.38541, 0.37123, 4000], # Philips TL84, Ultralume 40
	"F12":  [0.43695, 0.40441, 0.44256, 0.39717, 3000]  # Philips TL83, Ultralume 30
}

rgbspaces = {
	# brucelindbloom.com/WorkingSpaceInfo.html
	#
	# name              gamma  white  primaries
	#                          point  Rx      Ry      RY        Gx      Gy      GY        Bx      By      BY
	"Adobe RGB (1998)": [2.2,  "D65", 0.6400, 0.3300, 0.297361, 0.2100, 0.7100, 0.627355, 0.1500, 0.0600, 0.075285],
	"Apple RGB ":       [1.8,  "D65", 0.6250, 0.3400, 0.244634, 0.2800, 0.5950, 0.672034, 0.1550, 0.0700, 0.083332],
	"Best RGB":         [2.2,  "D50", 0.7347, 0.2653, 0.228457, 0.2150, 0.7750, 0.737352, 0.1300, 0.0350, 0.034191],
	"Beta RGB":         [2.2,  "D50", 0.6888, 0.3112, 0.303273, 0.1986, 0.7551, 0.663786, 0.1265, 0.0352, 0.032941],
	"Bruce RGB":        [2.2,  "D65", 0.6400, 0.3300, 0.240995, 0.2800, 0.6500, 0.683554, 0.1500, 0.0600, 0.075452],
	"CIE RGB":          [2.2,  "E",   0.7350, 0.2650, 0.176204, 0.2740, 0.7170, 0.812985, 0.1670, 0.0090, 0.010811],
	"ColorMatch RGB":   [1.8,  "D50", 0.6300, 0.3400, 0.274884, 0.2950, 0.6050, 0.658132, 0.1500, 0.0750, 0.066985],
	"Don RGB 4":        [2.2,  "D50", 0.6960, 0.3000, 0.278350, 0.2150, 0.7650, 0.687970, 0.1300, 0.0350, 0.033680],
	"ECI RGB":          [1.8,  "D50", 0.6700, 0.3300, 0.320250, 0.2100, 0.7100, 0.602071, 0.1400, 0.0800, 0.077679],
	"Ekta Space PS5":   [2.2,  "D50", 0.6950, 0.3050, 0.260629, 0.2600, 0.7000, 0.734946, 0.1100, 0.0050, 0.004425],
	"NTSC RGB":         [2.2,  "C",   0.6700, 0.3300, 0.298839, 0.2100, 0.7100, 0.586811, 0.1400, 0.0800, 0.114350],
	"PAL/SECAM RGB":    [2.2,  "D65", 0.6400, 0.3300, 0.222021, 0.2900, 0.6000, 0.706645, 0.1500, 0.0600, 0.071334],
	"ProPhoto RGB":     [1.8,  "D50", 0.7347, 0.2653, 0.288040, 0.1596, 0.8404, 0.711874, 0.0366, 0.0001, 0.000086],
	"SMPTE-C RGB":      [2.2,  "D65", 0.6300, 0.3400, 0.212395, 0.3100, 0.5950, 0.701049, 0.1550, 0.0700, 0.086556],
	"sRGB":             [2.2,  "D65", 0.6400, 0.3300, 0.212656, 0.3000, 0.6000, 0.715158, 0.1500, 0.0600, 0.072186],
	"Wide Gamut RGB":   [2.2,  "D50", 0.7350, 0.2650, 0.258187, 0.1150, 0.8260, 0.724938, 0.1570, 0.0180, 0.016875]
}


def cat_matrix(cat="Bradford"):
	if isinstance(cat, basestring):
		cat = cat_matrices[cat]
	if not isinstance(cat, Matrix3x3):
		cat = Matrix3x3(cat)
	return cat


def cbrt(x):
	return math.pow(x, 1.0 / 3.0) if x >= 0 else -math.pow(-x, 1.0 / 3.0)


def XYZ2LMS(X, Y, Z, cat="Bradford"):
	cat = cat_matrix(cat)
	p, y, b = cat * [X, Y, Z]
	return p, y, b


def LMS_wp_adaption_matrix(whitepoint_source=None, 
						   whitepoint_destination=None, 
						   cat="Bradford"):
	# chromatic adaption
	# based on formula http://brucelindbloom.com/Eqn_ChromAdapt.html
	# cat = adaption matrix or predefined choice ('CAT02', 'Bradford', 
	# 'Von Kries', 'XYZ Scaling', see cat_matrices), defaults to 'Bradford'
	cat = cat_matrix(cat)
	if isinstance(whitepoint_source, (list, tuple)):
		XYZWS = whitepoint_source
	elif whitepoint_source:
		XYZWS = CIEDCCT2XYZ(whitepoint_source)
	else:
		XYZWS = 0.96422, 1.0, 0.82521  # Observer= 2°, Illuminant= D50
	if isinstance(whitepoint_destination, (list, tuple)):
		XYZWD = whitepoint_destination
	elif whitepoint_destination:
		XYZWD = CIEDCCT2XYZ(whitepoint_destination)
	else:
		XYZWD = 0.96422, 1.0, 0.82521  # Observer= 2°, Illuminant= D50
	if XYZWS[1] <= 1.0 and XYZWD[1] > 1.0:
		# make sure the scaling is identical
		XYZWS = [v * 100 for v in XYZWS]
	if XYZWD[1] <= 1.0 and XYZWS[1] > 1.0:
		# make sure the scaling is identical
		XYZWD = [v * 100 for v in XYZWD]
	Ls, Ms, Ss = XYZ2LMS(XYZWS[0], XYZWS[1], XYZWS[2], cat)
	Ld, Md, Sd = XYZ2LMS(XYZWD[0], XYZWD[1], XYZWD[2], cat)
	return Matrix3x3([[Ld/Ls, 0, 0], [0, Md/Ms, 0], [0, 0, Sd/Ss]])


def wp_adaption_matrix(whitepoint_source=None, whitepoint_destination=None, 
					   cat="Bradford"):
	# chromatic adaption
	# based on formula http://brucelindbloom.com/Eqn_ChromAdapt.html
	# cat = adaption matrix or predefined choice ('CAT02', 'Bradford', 
	# 'Von Kries', 'XYZ Scaling', see cat_matrices), defaults to 'Bradford'
	cat = cat_matrix(cat)
	return cat.inverted() * LMS_wp_adaption_matrix(whitepoint_source, 
												   whitepoint_destination, 
												   cat) * cat


def adapt(X, Y, Z, whitepoint_source=None, whitepoint_destination=None, 
		  cat="Bradford"):
	# chromatic adaption
	# based on formula http://brucelindbloom.com/Eqn_ChromAdapt.html
	# cat = adaption matrix or predefined choice ('CAT02', 'Bradford', 
	# 'Von Kries', 'XYZ Scaling', see cat_matrices), defaults to 'Bradford'
	return wp_adaption_matrix(whitepoint_source, whitepoint_destination, 
							  cat) * (X, Y, Z)


def is_similar_matrix(matrix1, matrix2, digits=3):
	""" Compare two matrices and check if they are the same
	up to n digits after the decimal point """
	return matrix1.rounded(digits) == matrix2.rounded(digits)


def guess_cat(chad, whitepoint_source=None, whitepoint_destination=None):
	""" Try and guess the chromatic adaption transform used in a chromatic 
	adaption matrix as found in an ICC profile's 'chad' tag """
	if chad == [[1, 0, 0], [0, 1, 0], [0, 0, 1]]:
		return "None"
	for cat in cat_matrices:
		if is_similar_matrix((chad * cat_matrices[cat].inverted() * 
							  LMS_wp_adaption_matrix(whitepoint_destination, 
													 whitepoint_source, 
													 cat)).inverted(), 
							 cat_matrices[cat], 2):
			return cat


def CIEDCCT2xyY(T):
	"""
	Convert from CIE correlated daylight temperature to xyY.
	
	T = temperature in Kelvin.
	
	Derived from formula found on brucelindbloom.com
	
	"""
	if type(T) == str:
		T = T.upper()
		if T in CIEilluminants:
			return CIEilluminants[T][0:2] + [1.0]
		raise ValueError('Unrecognized color temperature "%s"' % T)
	if 4000 <= T and T <= 7000:
		xD = (((-4.607 * math.pow(10, 9)) / math.pow(T, 3))
			+ ((2.9678 * math.pow(10, 6)) / math.pow(T, 2))
			+ ((0.09911 * math.pow(10, 3)) / T)
			+ 0.244063)
	elif 7000 < T and T <= 25000:
		xD = (((-2.0064 * math.pow(10, 9)) / math.pow(T, 3))
			+ ((1.9018 * math.pow(10, 6)) / math.pow(T, 2))
			+ ((0.24748 * math.pow(10, 3)) / T)
			+ 0.237040)
	else:
		return None
	yD = -3 * math.pow(xD, 2) + 2.87 * xD - 0.275
	return xD, yD, 1.0


def CIEDCCT2XYZ(T):
	"""
	Convert from CIE correlated daylight temperature to XYZ.
	
	T = temperature in Kelvin.
	
	"""
	return xyY2XYZ(*CIEDCCT2xyY(T))


def get_DBL_MIN():
	t = "0.0"
	i = 10
	n = 0
	while True:
		if i > 1:
			i -= 1
		else:
			t += "0"
			i = 9
		if float(t + str(i)) == 0.0:
			if n > 1:
				break
			n += 1
			t += str(i)
			i = 10
		else:
			if n > 1:
				n -= 1
			DBL_MIN = float(t + str(i))
	return DBL_MIN


DBL_MIN = get_DBL_MIN()


def Lab2XYZ(L, a, b, whitepoint=None):
	"""
	based on formula
	http://brucelindbloom.com/Eqn_Lab_to_XYZ.html
	
	whitepoint can be a color temperature in Kelvin or an array containing 
	reference XYZ values. It defaults to D50
	
	Implementation Notes:
	The output XYZ values are in the nominal range [0.0, 1.0].
	
	"""
	fy = (L + 16) / 116.0
	fx = a / 500.0 + fy
	fz = fy - b / 200.0
	
	E = 0.008856
	K = 903.3
	
	if math.pow(fx, 3.0) > E:
		xr = math.pow(fx, 3.0)
	else:
		xr = (116.0 * fx - 16) / K
	
	if L > K * E:
		yr = math.pow((L + 16) / 116.0, 3.0)
	else:
		yr = L / K
	
	if math.pow(fz, 3.0) > E:
		zr = math.pow(fz, 3.0)
	else:
		zr = (116.0 * fz - 16) / K
	
	if whitepoint:
		if isinstance(whitepoint, (float, int)):
			Xr, Yr, Zr = CIEDCCT2XYZ(whitepoint)
		else:
			Xr, Yr, Zr = whitepoint
	else:
		Xr, Yr, Zr = 0.96422, 1.0, 0.82521  # Observer = 2°, Illuminant = D50
	
	X = xr * Xr
	Y = yr * Yr
	Z = zr * Zr
	
	return X, Y, Z


def RGB2XYZ(R, G, B, gamma=None, matrix=None):
	"""
	Convert from RGB to XYZ.
	
	Use optional gamma and matrix (both default to sRGB).
	
	Formula from brucelindbloom.com
	
	Implementation Notes:
	1. The transformation matrix [M] is calculated from the RGB reference 
	   primaries as discussed here:
	   http://brucelindbloom.com/Eqn_RGB_XYZ_Matrix.html
	2. The gamma values for many common RGB color spaces may be found here:
	   http://brucelindbloom.com/WorkingSpaceInfo.html#Specifications
	3. Your input RGB values may need to be scaled before using the above. 
	   For example, if your values are in the range [0, 255], you must first 
	   divide each by 255.0.
	4. The output XYZ values are in the nominal range [0.0, 1.0].
	5. The XYZ values will be relative to the same reference white as the 
	   RGB system. If you want XYZ relative to a different reference white, 
	   you must apply a chromatic adaptation transform 
	   [http://brucelindbloom.com/Eqn_ChromAdapt.html] to the XYZ color to 
	   convert it from the reference white of the RGB system to the desired 
	   reference white.
	6. Sometimes the more complicated special case of sRGB shown above is 
	   replaced by a "simplified" version using a straight gamma function 
	   with gamma = 2.2.
	   
	"""
	if gamma is None: # default to sRGB trc
		if R > 0.04045:
			R = math.pow((R + 0.055) / 1.055, 2.4)
		else:
			R = R / 12.92
		if G > 0.04045:
			G = math.pow((G + 0.055) / 1.055, 2.4)
		else:
			G = G / 12.92
		if B > 0.04045:
			B = math.pow((B + 0.055) / 1.055, 2.4)
		else:
			B = B / 12.92
	else:
		R = math.pow(R, gamma)
		G = math.pow(G, gamma)
		B = math.pow(B, gamma)
	if matrix is None: # default to sRGB matrix
		matrix = (
			(0.412424, 0.212656,  0.0193324),
			(0.357579, 0.715158,  0.119193),
			(0.180464, 0.0721856, 0.950444)
		)
	X = R * matrix[0][0] + G * matrix[1][0] + B * matrix[2][0]
	Y = R * matrix[0][1] + G * matrix[1][1] + B * matrix[2][1]
	Z = R * matrix[0][2] + G * matrix[1][2] + B * matrix[2][2]
	return X, Y, Z


def matrix_rgb(xr, yr, xg, yg, xb, yb, Xw, Yw, Zw):
	""" Create and return an RGB matrix. """
	Xr, Yr, Zr = xyY2XYZ(xr, yr, 1.0)
	Xg, Yg, Zg = xyY2XYZ(xg, yg, 1.0)
	Xb, Yb, Zb = xyY2XYZ(xb, yb, 1.0)
	mtx = numpy.matrix((
		(Xr, Yr, Zr),
		(Xg, Yg, Zg),
		(Xb, Yb, Zb)
	)).I
	Sr = Xw * mtx[0].item(0) + Yw * mtx[1].item(0) + Zw * mtx[2].item(0)
	Sg = Xw * mtx[0].item(1) + Yw * mtx[1].item(1) + Zw * mtx[2].item(1)
	Sb = Xw * mtx[0].item(2) + Yw * mtx[1].item(2) + Zw * mtx[2].item(2)
	return (
		(Sr * Xr, Sr * Yr, Sr * Zr),
		(Sg * Xg, Sg * Yg, Sg * Zg),
		(Sb * Xb, Sb * Yb, Sb * Zb)
	)


def planckianCT2XYZ(T):
	""" Convert from planckian temperature to XYZ.
	
	T = temperature in Kelvin.
	
	"""
	return xyY2XYZ(*planckianCT2xyY(T))


def planckianCT2xyY(T):
	""" Convert from planckian temperature to xyY.
	
	T = temperature in Kelvin.
	
	Formula from http://en.wikipedia.org/wiki/Planckian_locus
	
	"""
	if   1667 <= T and T <= 4000:
		x = (  -0.2661239 * (math.pow(10, 9) / math.pow(T, 3))
			 -  0.2343580 * (math.pow(10, 6) / math.pow(T, 2))
			 +  0.8776956 * (math.pow(10, 3) / T)
			 +  0.179910)
	elif 4000 <= T and T <= 25000:
		x = (  -3.0258469 * (math.pow(10, 9) / math.pow(T, 3))
			 +  2.1070379 * (math.pow(10, 6) / math.pow(T, 2))
			 +  0.2226347 * (math.pow(10, 3) / T)
			 +  0.24039)
	else:
		return None
	if   1667 <= T and T <= 2222:
		y = (  -1.1063814  * math.pow(x, 3)
			 -  1.34811020 * math.pow(x, 2)
			 +  2.18555832 * x
			 -  0.20219683)
	elif 2222 <= T and T <= 4000:
		y = (  -0.9549476  * math.pow(x, 3)
			 -  1.37418593 * math.pow(x, 2)
			 +  2.09137015 * x
			 -  0.16748867)
	elif 4000 <= T and T <= 25000:
		y = (   3.0817580  * math.pow(x, 3)
			 -  5.87338670 * math.pow(x, 2)
			 +  3.75112997 * x
			 -  0.37001483)
	return x, y, 1.0


def xyY2CCT(x, y, Y):
	""" Convert from xyY to correlated color temperature. """
	return XYZ2CCT(*xyY2XYZ(x, y, Y))


def xyY2XYZ(x, y, Y):
	"""
	Convert from xyY to XYZ.
	
	Formula from brucelindbloom.com
	
	Implementation Notes:
	1. Watch out for the case where y = 0. In that case, X = Y = Z = 0 is 
	   returned.
	2. The output XYZ values are in the nominal range [0.0, 1.0].
	
	"""
	if y == 0:
		return 0, 0, 0
	X = (x * Y) / y
	Z = ((1 - x - y) * Y) / y
	return X, Y, Z


def LERP(a,b,c):
	"""
	LERP(a,b,c) = linear interpolation macro.
	
	Is 'a' when c == 0.0 and 'b' when c == 1.0
	
	"""
	return (b - a) * c + a


def XYZ2CCT(X, Y, Z):
	"""
	Convert from XYZ to correlated color temperature.
	
	Derived from ANSI C implementation by Bruce Lindbloom brucelindbloom.com
	
	Return: correlated color temperature if successful, else None.
	
	Description:
	This is an implementation of Robertson's method of computing the 
	correlated color temperature of an XYZ color. It can compute correlated 
	color temperatures in the range [1666.7K, infinity].
	
	Reference:
	"Color Science: Concepts and Methods, Quantitative Data and Formulae", 
	Second Edition, Gunter Wyszecki and W. S. Stiles, John Wiley & Sons, 
	1982, pp. 227, 228.
	
	"""
	rt = [       # reciprocal temperature (K)
		 DBL_MIN,  10.0e-6,  20.0e-6,  30.0e-6,  40.0e-6,  50.0e-6,
		 60.0e-6,  70.0e-6,  80.0e-6,  90.0e-6, 100.0e-6, 125.0e-6,
		150.0e-6, 175.0e-6, 200.0e-6, 225.0e-6, 250.0e-6, 275.0e-6,
		300.0e-6, 325.0e-6, 350.0e-6, 375.0e-6, 400.0e-6, 425.0e-6,
		450.0e-6, 475.0e-6, 500.0e-6, 525.0e-6, 550.0e-6, 575.0e-6,
		600.0e-6
	]
	uvt = [
		[0.18006, 0.26352, -0.24341],
		[0.18066, 0.26589, -0.25479],
		[0.18133, 0.26846, -0.26876],
		[0.18208, 0.27119, -0.28539],
		[0.18293, 0.27407, -0.30470],
		[0.18388, 0.27709, -0.32675],
		[0.18494, 0.28021, -0.35156],
		[0.18611, 0.28342, -0.37915],
		[0.18740, 0.28668, -0.40955],
		[0.18880, 0.28997, -0.44278],
		[0.19032, 0.29326, -0.47888],
		[0.19462, 0.30141, -0.58204],
		[0.19962, 0.30921, -0.70471],
		[0.20525, 0.31647, -0.84901],
		[0.21142, 0.32312, -1.0182],
		[0.21807, 0.32909, -1.2168],
		[0.22511, 0.33439, -1.4512],
		[0.23247, 0.33904, -1.7298],
		[0.24010, 0.34308, -2.0637],
		[0.24792, 0.34655, -2.4681],	# Note: 0.24792 is a corrected value 
										# for the error found in W&S as 0.24702
		[0.25591, 0.34951, -2.9641],
		[0.26400, 0.35200, -3.5814],
		[0.27218, 0.35407, -4.3633],
		[0.28039, 0.35577, -5.3762],
		[0.28863, 0.35714, -6.7262],
		[0.29685, 0.35823, -8.5955],
		[0.30505, 0.35907, -11.324],
		[0.31320, 0.35968, -15.628],
		[0.32129, 0.36011, -23.325],
		[0.32931, 0.36038, -40.770],
		[0.33724, 0.36051, -116.45]
	]
	if ((X < 1.0e-20) and (Y < 1.0e-20) and (Z < 1.0e-20)):
		return None	# protect against possible divide-by-zero failure
	us = (4.0 * X) / (X + 15.0 * Y + 3.0 * Z)
	vs = (6.0 * Y) / (X + 15.0 * Y + 3.0 * Z)
	dm = 0.0
	i = 0
	while i < 31:
		di = (vs - uvt[i][1]) - uvt[i][2] * (us - uvt[i][0])
		if i > 0 and ((di < 0.0 and dm >= 0.0) or (di >= 0.0 and dm < 0.0)):
			break	# found lines bounding (us, vs) : i-1 and i
		dm = di
		i += 1
	if (i == 31):
		# bad XYZ input, color temp would be less than minimum of 1666.7 
		# degrees, or too far towards blue
		return None
	di = di / math.sqrt(1.0 + uvt[i    ][2] * uvt[i    ][2])
	dm = dm / math.sqrt(1.0 + uvt[i - 1][2] * uvt[i - 1][2])
	p = dm / (dm - di)	# p = interpolation parameter, 0.0 : i-1, 1.0 : i
	p = 1.0 / (LERP(rt[i - 1], rt[i], p))
	return p


def XYZ2Lab(X, Y, Z, Xr=None, Yr=None, Zr=None):
	"""
	based on formula from www.brucelindbloom.com
	Xr, Yr, Zr = reference whitepoint -or- Xr = reference color temperature in 
	Kelvin
	
	"""
	if Yr is None or Zr is None:
		if Xr is None:
			Xr = "D50"
		if isinstance(Xr, basestring):
			if Xr == "A":
				Xr = 109.828
				Yr = 35.547
			elif Xr == "B":
				Xr = 99.072
				Yr = 85.223
			elif Xr == "C":
				Xr = 98.041
				Yr = 118.103
			elif Xr == "D55":
				Xr = 95.642
				Zr = 92.085
			elif Xr == "D65":
				Xr = 95.0467
				Yr = 108.8969
			elif Xr == "D75":
				Xr = 94.939
				Yr = 122.558
			elif Xr == "E":
				Xr = 100.0
				Yr = 100.0
			else:
				Xr = 96.422
				Zr = 82.521
			Yr = 100.0
		else:
			xyY = CIEDCCT2xyY(Xr, True)
			XYZ = xyY2XYZ(xyY[0], xyY[1], xyY[2])
			Xr = XYZ[0]
			Yr = XYZ[1]
			Zr = XYZ[2]

	E = 0.008856
	K = 903.3
	xr = X / Xr
	yr = Y / Yr
	zr = Z / Zr
	fx = cbrt(xr) if xr > E else (K * xr + 16) / 116.0
	fy = cbrt(yr) if yr > E else (K * yr + 16) / 116.0
	fz = cbrt(zr) if zr > E else (K * zr + 16) / 116.0
	L = 116 * fy - 16
	a = 500 * (fx - fy)
	b = 200 * (fy - fz)
	
	return L, a, b


def XYZ2RGB(X, Y, Z, gamma=None, matrix=None):
	"""
	Convert from XYZ to RGB.
	
	Formula from brucelindbloom.com
	
	Implementation Notes:
	1. The transformation matrix [M] is calculated from the RGB reference 
	   primaries as discussed here:
	   http://brucelindbloom.com/Eqn_RGB_XYZ_Matrix.html
	2. gamma is the gamma value of the RGB color system used. Many common ones 
	   may be found here:
	   http://brucelindbloom.com/WorkingSpaceInfo.html#Specifications
	3. The output RGB values are in the nominal range [0.0, 1.0]. You may wish 
	   to scale them to some other range. For example, if you want RGB in the 
	   range [0, 255], you must multiply each component by 255.0.
	4. If the input XYZ color is not relative to the same reference white as 
	   the RGB system, you must first apply a chromatic adaptation transform 
	   [http://brucelindbloom.com/Eqn_ChromAdapt.html] to the XYZ color to 
	   convert it from its own reference white to the reference white of the 
	   RGB system.
	5. Sometimes the more complicated special case of sRGB shown above is 
	   replaced by a "simplified" version using a straight gamma function with 
	   gamma = 2.2.
	
	"""
	if matrix is None: # default to sRGB matrix
		matrix = (
			( 3.24071,  -0.969258,   0.0556352),
			(-1.53726,   1.87599,   -0.203996),
			(-0.498571,  0.0415557,  1.05707)
		)
	R = X * matrix[0][0] + Y * matrix[1][0] + Z * matrix[2][0]
	G = X * matrix[0][1] + Y * matrix[1][1] + Z * matrix[2][1]
	B = X * matrix[0][2] + Y * matrix[1][2] + Z * matrix[2][2]
	if gamma is None: # default to sRGB trc
		if (R > 0.0031308):
			R = 1.055 * math.pow(R, 1.0 / 2.4) - 0.055
		else:
			R = 12.92 * R
		if (G > 0.0031308):
			G = 1.055 * math.pow(G, 1.0 / 2.4) - 0.055
		else:
			G = 12.92 * G
		if (B > 0.0031308):
			B = 1.055 * math.pow(B, 1.0 / 2.4) - 0.055
		else:
			B = 12.92 * B
	else:
		R = math.pow(R, 1.0 / gamma)
		G = math.pow(G, 1.0 / gamma)
		B = math.pow(B, 1.0 / gamma)
	R = max(0.0, R)
	G = max(0.0, G)
	B = max(0.0, B)
	R = min(1.0, R)
	G = min(1.0, G)
	B = min(1.0, B)
	return R, G, B


def XYZ2xyY(X, Y, Z):
	"""
	Convert from XYZ to xyY.
	
	Formula from brucelindbloom.com
	
	Implementation Notes:
	1. Watch out for black, where X = Y = Z = 0. In that case, x and y are set 
	   to the chromaticity coordinates of D50.
	2. The output Y value is in the nominal range [0.0, 1.0].
	
	"""
	if X == Y == Z == 0:
		return CIEDCCT2xyY(5000)[0:2] + (0, )
	x = X / (X + Y + Z)
	y = Y / (X + Y + Z)
	return x, y, Y


class Matrix3x3(list):
	
	""" Simple 3x3 matrix """
	
	def __init__(self, matrix=None):
		if matrix:
			self.update(matrix)
	
	def update(self, matrix):
		if len(matrix) != 3:
			raise ValueError('Invalid number of rows for 3x3 matrix: %i' % len(matrix))
		while len(self):
			self.pop()
		for row in matrix:
			if len(row) != 3:
				raise ValueError('Invalid number of columns for 3x3 matrix: %i' % len(row))
			self.append([]);
			for column in row:
				self[-1].append(column)
	
	def __add__(self, matrix):
		instance = self.__class__()
		instance.update([[self[0][0] + matrix[0][0],
								self[0][1] + matrix[0][1],
								self[0][2] + matrix[0][2]],
							   [self[1][0] + matrix[1][0],
								self[1][1] + matrix[1][1],
								self[1][2] + matrix[1][2]],
							   [self[2][0] + matrix[2][0],
								self[2][1] + matrix[2][1],
								self[2][2] + matrix[2][2]]])
		return instance
	
	def __iadd__(self, matrix):
		# inplace
		self.update(self.__add__(matrix))
		return self
	
	def __imul__(self, matrix):
		# inplace
		self.update(self.__mul__(matrix))
		return self
	
	def __mul__(self, matrix):
		if not isinstance(matrix[0], (list, tuple)):
			return [matrix[0] * self[0][0] + matrix[1] * self[0][1] + matrix[2] * self[0][2],
					matrix[0] * self[1][0] + matrix[1] * self[1][1] + matrix[2] * self[1][2],
					matrix[0] * self[2][0] + matrix[1] * self[2][1] + matrix[2] * self[2][2]]
		instance = self.__class__()
		instance.update([[self[0][0]*matrix[0][0] + self[0][1]*matrix[1][0] + self[0][2]*matrix[2][0],
								self[0][0]*matrix[0][1] + self[0][1]*matrix[1][1] + self[0][2]*matrix[2][1],
								self[0][0]*matrix[0][2] + self[0][1]*matrix[1][2] + self[0][2]*matrix[2][2]],
							   [self[1][0]*matrix[0][0] + self[1][1]*matrix[1][0] + self[1][2]*matrix[2][0],
								self[1][0]*matrix[0][1] + self[1][1]*matrix[1][1] + self[1][2]*matrix[2][1],
								self[1][0]*matrix[0][2] + self[1][1]*matrix[1][2] + self[1][2]*matrix[2][2]],
							   [self[2][0]*matrix[0][0] + self[2][1]*matrix[1][0] + self[2][2]*matrix[2][0],
								self[2][0]*matrix[0][1] + self[2][1]*matrix[1][1] + self[2][2]*matrix[2][1],
								self[2][0]*matrix[0][2] + self[2][1]*matrix[1][2] + self[2][2]*matrix[2][2]]])
		return instance
	
	def adjoint(self):
		return self.cofactors().transposed()
	
	def cofactors(self):
		instance = self.__class__()
		instance.update([[(self[1][1]*self[2][2] - self[1][2]*self[2][1]),
								-1 * (self[1][0]*self[2][2] - self[1][2]*self[2][0]),
								(self[1][0]*self[2][1] - self[1][1]*self[2][0])],
							   [-1 * (self[0][1]*self[2][2] - self[0][2]*self[2][1]),
								(self[0][0]*self[2][2] - self[0][2]*self[2][0]),
								-1 * (self[0][0]*self[2][1] -self[0][1]*self[2][0])],
							   [(self[0][1]*self[1][2] - self[0][2]*self[1][1]),
								-1 * (self[0][0]*self[1][2] - self[1][0]*self[0][2]),
								(self[0][0]*self[1][1] - self[0][1]*self[1][0])]])
		return instance
	
	def determinant(self):
		return ((self[0][0]*self[1][1]*self[2][2] + 
				 self[1][0]*self[2][1]*self[0][2] + 
				 self[0][1]*self[1][2]*self[2][0]) - 
				(self[2][0]*self[1][1]*self[0][2] + 
				 self[1][0]*self[0][1]*self[2][2] + 
				 self[2][1]*self[1][2]*self[0][0]))
	
	def invert(self):
		# inplace
		self.update(self.inverted())
	
	def inverted(self):
		determinant = self.determinant()
		matrix = self.adjoint()
		instance = self.__class__()
		instance.update([[matrix[0][0] / determinant,
								matrix[0][1] / determinant,
								matrix[0][2] / determinant],
							   [matrix[1][0] / determinant,
								matrix[1][1] / determinant,
								matrix[1][2] / determinant],
							   [matrix[2][0] / determinant,
								matrix[2][1] / determinant,
								matrix[2][2] / determinant]])
		return instance
	
	def rounded(self, digits=3):
		matrix = self.__class__()
		for row in self:
			matrix.append([]);
			for column in row:
				matrix[-1].append(round(column, digits))
		return matrix
								
	def transpose(self):
		self.update(self.transposed())
	
	def transposed(self):
		instance = self.__class__()
		instance.update([[self[0][0], self[1][0], self[2][0]],
							   [self[0][1], self[1][1], self[2][1]],
							   [self[0][2], self[1][2], self[2][2]]])
		return instance


# Chromatic adaption transform matrices
# Bradford, von Kries from http://brucelindbloom.com/Eqn_ChromAdapt.html
# CAT02 from http://en.wikipedia.org/wiki/CIECAM02#CAT02
# HPE, CAT97s from http://en.wikipedia.org/wiki/LMS_color_space#CAT97s
# CMCCAT97 from 'Performance Of Five Chromatic Adaptation Transforms Using 
# Large Number Of Color Patches', http://hrcak.srce.hr/file/95370
# CMCCAT2000, Sharp from 'Computational colour science using MATLAB'
# ISBN 0470845627, http://books.google.com/books?isbn=0470845627
# Cross-verification of the matrix numbers has been done using various sources,
# most notably 'Chromatic Adaptation Performance of Different RGB Sensors'
# http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.14.918&rep=rep1&type=pdf
cat_matrices = {"Bradford": Matrix3x3([[ 0.89510,  0.26640, -0.16140],
									   [-0.75020,  1.71350,  0.03670],
									   [ 0.03890, -0.06850,  1.02960]]),
				"CAT02": Matrix3x3([[ 0.7328,  0.4296, -0.1624],
									[-0.7036,  1.6975,  0.0061],
									[ 0.0030,  0.0136,  0.9834]]),
				"CAT97s": Matrix3x3([[ 0.8562,  0.3372, -0.1934],
									 [-0.8360,  1.8327,  0.0033],
									 [ 0.0357, -0.0469,  1.0112]]),
				"CMCCAT97": Matrix3x3([[ 0.8951, -0.7502,  0.0389],
									   [ 0.2664,  1.7135,  0.0685],
									   [-0.1614,  0.0367,  1.0296]]),
				"CMCCAT2000": Matrix3x3([[ 0.7982,  0.3389, -0.1371],
										 [-0.5918,  1.5512,  0.0406],
										 [ 0.0008,  0.0239,  0.9753]]),
				# Hunt-Pointer-Estevez, equal-energy illuminant 
				"HPE normalized to illuminant E": Matrix3x3([[ 0.38971, 0.68898, -0.07868],
								  [-0.22981, 1.18340,  0.04641],
								  [ 0.00000, 0.00000,  1.00000]]),
				# Süsstrunk et al.15 optimized spectrally sharpened matrix
				"Sharp": Matrix3x3([[ 1.2694, -0.0988, -0.1706],
									[-0.8364,  1.8006,  0.0357],
									[ 0.0297, -0.0315,  1.0018]]),
				# 'Von Kries' as found on Bruce Lindbloom's site: 
				# Hunt-Pointer-Estevez normalized to D65
				# (maybe I should call it that instead of 'Von Kries'
				# to avoid ambiguity?)
				"HPE normalized to illuminant D65": Matrix3x3([[ 0.40024,  0.70760, -0.08081],
										[-0.22630,  1.16532,  0.04570],
										[ 0.00000,  0.00000,  0.91822]]),
				"RLAB": Matrix3x3([[1.9569, -1.1882, 0.2313], 
								   [0.3612, 0.6388, 0.0], 
								   [0.0, 0.0, 1.0]]).inverted(),
				"XYZ scaling": Matrix3x3([[1, 0, 0],
										  [0, 1, 0],
										  [0, 0, 1]])}


def test():
	for i in range(4):
		if i == 0:
			wp = "native"
		elif i == 1:
			wp = "D50"
			XYZ = CIEDCCT2XYZ(wp)
		elif i == 2:
			wp = "D65"
			XYZ = CIEDCCT2XYZ(wp)
		elif i == 3:
			XYZ = (0.95106486, 1.0, 1.08844025)
			wp = " ".join([str(v) for v in XYZ])
		print ("RGB and corresponding XYZ (nominal range 0.0 - 1.0) with "
			   "whitepoint %s" % wp)
		for name in rgbspaces:
			spc = rgbspaces[name]
			if i == 0:
				XYZ = CIEDCCT2XYZ(spc[1])
			mtx = matrix_rgb(spc[2], spc[3], spc[5], spc[6], spc[8], spc[9], 
							 *XYZ)
			print "%s 1.0, 1.0, 1.0 = XYZ" % name, \
				[str(round(v, 4)) for v in RGB2XYZ(1.0, 1.0, 1.0, spc[0], mtx)]
			print "%s 1.0, 0.0, 0.0 = XYZ" % name, \
				[str(round(v, 4)) for v in RGB2XYZ(1.0, 0.0, 0.0, spc[0], mtx)]
			print "%s 0.0, 1.0, 0.0 = XYZ" % name, \
				[str(round(v, 4)) for v in RGB2XYZ(0.0, 1.0, 0.0, spc[0], mtx)]
			print "%s 0.0, 0.0, 1.0 = XYZ" % name, \
				[str(round(v, 4)) for v in RGB2XYZ(0.0, 0.0, 1.0, spc[0], mtx)]
		print ""

if __name__ == '__main__':
	test()