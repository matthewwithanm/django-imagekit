#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ICCProfile.py

Adapted from the excellent ICCProfile python class by Florian Höch,
which is a part of the source of dispcalGUI:

	http://dispcalgui.hoech.net/

Copyright (c) 2011 OST, LLC. 
"""
import locale, math, sys, os, re, struct, base64
from hashlib import md5
from time import localtime, mktime, strftime
from UserString import UserString
from encoding import get_encodings
from ordereddict import OrderedDict

try:
	from jogging import logging
except ImportError:
	safe_print = lambda s: sys.stdout.echo(u"%s\n" % s)
else:
	safe_print = lambda s: logging.info(s)

# Keep this off -- trust me.
#from django.conf import settings
#debug = getattr(settings, 'DEBUG', False)
debug = False

fs_enc = get_encodings()[1]

encodings = {
	"mac": {
		141: "africaans",
		36: "albanian",
		85: "amharic",
		12: "arabic",
		51: "armenian",
		68: "assamese",
		134: "aymara",
		49: "azerbaijani-cyrllic",
		50: "azerbaijani-arabic",
		129: "basque",
		67: "bengali",
		137: "dzongkha",
		142: "breton",
		44: "bulgarian",
		77: "burmese",
		46: "byelorussian",
		78: "khmer",
		130: "catalan",
		92: "chewa",
		33: "simpchinese",
		19: "tradchinese",
		18: "croatian",
		38: "czech",
		7: "danish",
		4: "dutch",
		0: "roman",
		94: "esperanto",
		27: "estonian",
		30: "faeroese",
		31: "farsi",
		13: "finnish",
		34: "flemish",
		1: "french",
		140: "galician",
		144: "scottishgaelic",
		145: "manxgaelic",
		52: "georgian",
		2: "german",
		14: "greek-monotonic",
		148: "greek-polytonic",
		133: "guarani",
		69: "gujarati",
		10: "hebrew",
		21: "hindi",
		26: "hungarian",
		15: "icelandic",
		81: "indonesian",
		143: "inuktitut",
		35: "irishgaelic",
		146: "irishgaelic-dotsabove",
		3: "italian",
		11: "japanese",
		138: "javaneserom",
		73: "kannada",
		61: "kashmiri",
		48: "kazakh",
		90: "kiryarwanda",
		54: "kirghiz",
		91: "rundi",
		23: "korean",
		60: "kurdish",
		79: "lao",
		131: "latin",
		28: "latvian",
		24: "lithuanian",
		43: "macedonian",
		93: "malagasy",
		83: "malayroman-latin",
		84: "malayroman-arabic",
		72: "malayalam",
		16: "maltese",
		66: "marathi",
		53: "moldavian",
		57: "mongolian",
		58: "mongolian-cyrillic",
		64: "nepali",
		9: "norwegian",
		71: "oriya",
		87: "oromo",
		59: "pashto",
		25: "polish",
		8: "portuguese",
		70: "punjabi",
		132: "quechua",
		37: "romanian",
		32: "russian",
		29: "sami",
		65: "sanskrit",
		42: "serbian",
		62: "sindhi",
		76: "sinhalese",
		39: "slovak",
		40: "slovenian",
		88: "somali",
		6: "spanish",
		139: "sundaneserom",
		89: "swahili",
		5: "swedish",
		82: "tagalog",
		55: "tajiki",
		74: "tamil",
		135: "tatar",
		75: "telugu",
		22: "thai",
		63: "tibetan",
		86: "tigrinya",
		147: "tongan",
		17: "turkish",
		56: "turkmen",
		136: "uighur",
		45: "ukrainian",
		20: "urdu",
		47: "uzbek",
		80: "vietnamese",
		128: "welsh",
		41: "yiddish"
	}
}

colorants = {
	0: {
		"description": "unknown"
		},
	1: {
		"description": "ITU-R BT.709",
		"channels": ((0.64, 0.33), (0.3, 0.6), (0.15, 0.06))
		},
	2: {
		"description": "SMPTE RP145-1994",
		"channels": ((0.63, 0.34), (0.31, 0.595), (0.155, 0.07))
		},
	3: {
		"description": "EBU Tech.3213-E",
		"channels": ((0.64, 0.33), (0.29, 0.6), (0.15, 0.06))
		},
	4: {
		"description": "P22",
		"channels": ((0.625, 0.34), (0.28, 0.605), (0.155, 0.07))
		}
}

geometry = {
	0: "unknown",
	1: "0/45 or 45/0",
	2: "0/d or d/0"
}

illuminants = {
	0: "unknown",
	1: "D50",
	2: "D65",
	3: "D93",
	4: "F2",
	5: "D55",
	6: "A",
	7: "E",
	8: "F8"
}

observers = {
	0: "unknown",
	1: "CIE 1931",
	2: "CIE 1964"
}

technology = {
	'AMD ': "Active Matrix Display",
	'CRT ': "Cathode Ray Tube Display",
	'KPCD': "Photo CD",
	'PMD ': "Passive Matrix Display",
	'dcam': "Digital Camera",
	'dcpj': "Digital Cinema Projector",
	'dmpc': "Digital Motion Picture Camera",
	'dsub': "Dye Sublimation Printer",
	'epho': "Electrophotographic Printer",
	'esta': "Electrostatic Printer",
	'flex': "Flexography",
	'fprn': "Film Writer",
	'fscn': "Film Scanner",
	'grav': "Gravure",
	'ijet': "Ink Jet Printer",
	'imgs': "Photo Image Setter",
	'mpfr': "Motion Picture Film Recorder",
	'mpfs': "Motion Picture Film Scanner",
	'offs': "Offset Lithography",
	'pjtv': "Projection Television",
	'rpho': "Photographic Paper Printer",
	'rscn': "Reflective Scanner",
	'silk': "Silkscreen",
	'twax': "Thermal Wax Printer",
	'vidc': "Video Camera",
	'vidm': "Video Monitor"
}


def Property(func):
	return property(**func())


def dateTimeNumber(binaryString):
	"""
	Byte
	Offset Content									   Encoded as...
	0..1   number of the year (actual year, e.g. 1994) uInt16Number
	2..3   number of the month (1-12)				   uInt16Number
	4..5   number of the day of the month (1-31)	   uInt16Number
	6..7   number of hours (0-23)					   uInt16Number
	8..9   number of minutes (0-59)					   uInt16Number
	10..11 number of seconds (0-59)					   uInt16Number
	"""
	Y, m, d, H, M, S = [uInt16Number(chunk) for chunk in (binaryString[:2], 
														  binaryString[2:4], 
														  binaryString[4:6], 
														  binaryString[6:8], 
														  binaryString[8:10], 
														  binaryString[10:12])]
	return Y, m, d, H, M, S


def s15Fixed16Number(binaryString):
	return struct.unpack(">i", binaryString)[0] / 65536.0


def s15Fixed16Number_tohex(num):
	return struct.pack(">i", num * 65536)


def u16Fixed16Number(binaryString):
	return struct.unpack(">I", binaryString)[0] / 65536.0


def u16Fixed16Number_tohex(num):
	return struct.pack(">I", int(num * 65536))


def u8Fixed8Number(binaryString):
	return struct.unpack(">H", binaryString)[0] / 256.0


def u8Fixed8Number_tohex(num):
	return struct.pack(">H", int(num * 256))


def uInt16Number(binaryString):
	return struct.unpack(">H", binaryString)[0]


def uInt16Number_tohex(num):
	return struct.pack(">H", num)


def uInt32Number(binaryString):
	return struct.unpack(">I", binaryString)[0]


def uInt32Number_tohex(num):
	return struct.pack(">I", num)


def uInt64Number(binaryString):
	return struct.unpack(">Q", binaryString)[0]


def uInt64Number_tohex(num):
	return struct.pack(">Q", num)


def uInt8Number(binaryString):
	return struct.unpack(">H", "\0" + binaryString)[0]


def uInt8Number_tohex(num):
	return struct.pack(">H", num)[1]


def videoCardGamma(tagData, tagSignature):
	reserved = uInt32Number(tagData[4:8])
	tagType = uInt32Number(tagData[8:12])
	if tagType == 0: # table
		return VideoCardGammaTableType(tagData, tagSignature)
	elif tagType == 1: # formula
		return VideoCardGammaFormulaType(tagData, tagSignature)




class CRInterpolation(object):

	"""
	Catmull-Rom interpolation.
	Curve passes through the points exactly, with neighbouring points influencing curvature.
	points[] should be at least 3 points long.
	"""

	def __init__(self, points):
		self.points = points

	def __call__(self, pos):
		lbound = int(math.floor(pos) - 1)
		ubound = int(math.ceil(pos) + 1)
		t = pos % 1.0
		if abs((lbound + 1) - pos) < 0.0001:
			# sitting on a datapoint, so just return that
			return self.points[lbound + 1]
		if lbound < 0:
			p = self.points[:ubound + 1]
			# extend to the left linearly
			while len(p) < 4:
				p.insert(0, p[0] - (p[1] - p[0]))
		else:
			p = self.points[lbound:ubound + 1]
			# extend to the right linearly
			while len(p) < 4:
				p.append(p[-1] - (p[-2] - p[-1]))
		t2 = t * t
		return 0.5 * ((2 * p[1]) + (-p[0] + p[2]) * t + 
					  ((2 * p[0]) - (5 * p[1]) + (4 * p[2]) - p[3]) * t2 +
					  (-p[0] + (3 * p[1]) - (3 * p[2]) + p[3]) * (t2 * t))


class ADict(dict):

	"""
	Convenience class for dictionary key access via attributes.
	
	Instead of writing aodict[key], you can also write aodict.key
	
	"""

	def __init__(self, *args, **kwargs):
		dict.__init__(self, *args, **kwargs)

	def __getattr__(self, name):
		if name in self:
			return self[name]
		else:
			raise AttributeError(name)

	def __setattr__(self, name, value):
		self[name] = value


class AODict(ADict, OrderedDict):

	def __init__(self, *args, **kwargs):
		OrderedDict.__init__(self, *args, **kwargs)

	def __setattr__(self, name, value):
		if name == "_keys":
			object.__setattr__(self, name, value)
		else:
			self[name] = value


class ICCProfileTag(object):

	def __init__(self, tagData, tagSignature):
		self.tagData = tagData
		self.tagSignature = tagSignature

	def __setattr__(self, name, value):
		if not isinstance(self, dict) or name in ("_keys", "tagData", 
												  "tagSignature"):
			object.__setattr__(self, name, value)
		else:
			self[name] = value
	
	def __repr__(self):
		"""
		t.__repr__() <==> repr(t)
		"""
		if isinstance(self, ADict):
			return ADict.__repr__(self)
		elif isinstance(self, UserString):
			return UserString.__repr__(self)
		elif isinstance(self, list):
			return list.__repr__(self)
		else:
			if not self:
				return "%s.%s()" % (self.__class__.__module__, self.__class__.__name__)
			return "%s.%s(%r)" % (self.__class__.__module__, self.__class__.__name__, self.tagData)


class Text(ICCProfileTag, UserString, str):

	def __init__(self, seq):
		UserString.__init__(self, seq)

	def __unicode__(self):
		return unicode(self.data, fs_enc, errors="replace")


class Colorant(ADict):

	def __init__(self, binaryString):
		self.type = uInt32Number(binaryString)
		self.channels = colorants[self.type].channels
		self.description = colorants[self.type].description


class Geometry(ADict):

	def __init__(self, binaryString):
		self.type = uInt32Number(binaryString)
		self.description = geometry[self.type]


class Illuminant(ADict):

	def __init__(self, binaryString):
		self.type = uInt32Number(binaryString)
		self.description = illuminants[self.type]


class Observer(ADict):

	def __init__(self, binaryString):
		self.type = uInt32Number(binaryString)
		self.description = observers[self.type]


class ChromacityType(ICCProfileTag, ADict):

	def __init__(self, tagData, tagSignature):
		ICCProfileTag.__init__(self, tagData, tagSignature)
		deviceChannelsCount = uInt16Number(tagData[8:10])
		colorant = uInt16Number(tagData[10:12])
		if colorant in colorants:
			colorant = colorants[colorant]
		channels = tagData[12:]
		self.colorant = colorant
		self.channels = []
		while channels:
			self.channels.append((u16Fixed16Number(channels[:4]), 
								  u16Fixed16Number(channels[4:8])))
			channels = channels[8:]


class CurveType(ICCProfileTag, list):

	def __init__(self, tagData, tagSignature):
		ICCProfileTag.__init__(self, tagData, tagSignature)
		curveEntriesCount = uInt32Number(tagData[8:12])
		curveEntries = tagData[12:]
		if curveEntriesCount == 1:
			# gamma
			self.append(u8Fixed8Number(curveEntries[:2]))
		else:
			# curve
			while curveEntries:
				self.append(uInt16Number(curveEntries[:2]))
				curveEntries = curveEntries[2:]


class DateTimeType(ICCProfileTag, list):

	def __init__(self, tagData, tagSignature):
		ICCProfileTag.__init__(self, tagData, tagSignature)
		self += dateTimeNumber(tagData[8:20])


class MeasurementType(ICCProfileTag, ADict):

	def __init__(self, tagData, tagSignature):
		ICCProfileTag.__init__(self, tagData, tagSignature)
		self.update({
			"observer": Observer(tagData[8:12]),
			"backing": XYZNumber(tagData[12:24]),
			"geometry": Geometry(tagData[24:28]),
			"flare": u16Fixed16Number(tagData[28:32]),
			"illuminantType": Illuminant(tagData[32:36])
		})


class MultiLocalizedUnicodeType(ICCProfileTag, AODict): # ICC v4

	def __init__(self, tagData, tagSignature):
		ICCProfileTag.__init__(self, tagData, tagSignature)
		AODict.__init__(self)
		recordsCount = uInt32Number(tagData[8:12])
		recordSize = uInt32Number(tagData[12:16]) # 12
		records = tagData[16:16 + recordSize * recordsCount]
		while records:
			record = records[:recordSize]
			recordLanguageCode = record[:2]
			recordCountryCode = record[2:4]
			recordLength = uInt32Number(record[4:8])
			recordOffset = uInt32Number(record[8:12])
			if recordLanguageCode not in self:
				self[recordLanguageCode] = AODict()
			self[recordLanguageCode][recordCountryCode] = unicode(
				tagData[recordOffset:recordOffset + recordLength], 
				"utf-16-be", "replace")
			records = records[recordSize:]

	def __str__(self):
		return unicode(self).encode(sys.getdefaultencoding())

	def __unicode__(self):
		"""
		Return tag as string.
		"""
		# TODO: Needs some work re locales
		# (currently if en-UK or en-US is not found, simply the first entry 
		# is returned)
		if "en" in self:
			for countryCode in ("UK", "US"):
				if countryCode in self["en"]:
					return self["en"][countryCode]
		return self.values()[0].values()[0]


class s15Fixed16ArrayType(ICCProfileTag, list):

	def __init__(self, tagData, tagSignature):
		ICCProfileTag.__init__(self, tagData, tagSignature)
		data = self.tagData[8:]
		while data:
			self.append(s15Fixed16Number(data[0:4]))
			data = data[4:]


def SignatureType(tagData, tagSignature):
	tag = Text(tagData[8:12].rstrip("\0"))
	tag.tagData = tagData
	tag.tagSignature = tagSignature
	return tag


class TextDescriptionType(ICCProfileTag, ADict): # ICC v2

	def __init__(self, tagData, tagSignature):
		ICCProfileTag.__init__(self, tagData, tagSignature)
		self.ASCII = ""
		if not tagData:
			return
		ASCIIDescriptionLength = uInt32Number(tagData[8:12])
		if ASCIIDescriptionLength:
			ASCIIDescription = tagData[12:12 + 
									   ASCIIDescriptionLength].strip("\0\n\r ")
			if ASCIIDescription:
				self.ASCII = ASCIIDescription
		unicodeOffset = 12 + ASCIIDescriptionLength
		self.unicodeLanguageCode = uInt32Number(
									tagData[unicodeOffset:unicodeOffset + 4])
		unicodeDescriptionLength = uInt32Number(tagData[unicodeOffset + 
														4:unicodeOffset + 8])
		if unicodeDescriptionLength:
			if unicodeOffset + 8 + unicodeDescriptionLength * 2 > len(tagData):
				# Damn you MS. The Unicode character count should be the number of 
				# double-byte characters (including trailing unicode NUL), not the
				# number of bytes as in the profiles created by Vista and later
				safe_print("Warning (non-critical): '%s' Unicode part end points "
						   "past the tag data, assuming number of bytes instead "
						   "of number of characters for length" % tagData[:4])
				unicodeDescriptionLength /= 2
			if tagData[unicodeOffset + 8 + 
					   unicodeDescriptionLength:unicodeOffset + 8 + 
					   unicodeDescriptionLength + 2] == "\0\0":
				safe_print("Warning (non-critical): '%s' Unicode part "
						   "seems to be a single-byte string (double-byte "
						   "string expected)" % tagData[:4])
				charBytes = 1 # fix for fubar'd desc
			else:
				charBytes = 2
			unicodeDescription = tagData[unicodeOffset + 8:unicodeOffset + 8 + 
										 (unicodeDescriptionLength) * charBytes]
			try:
				if charBytes == 1:
					unicodeDescription = unicode(unicodeDescription, 
												 errors="replace")
				else:
					if unicodeDescription[:2] == "\xfe\xff":
						# UTF-16 Big Endian
						if debug: safe_print("UTF-16 Big endian")
						unicodeDescription = unicodeDescription[2:]
						if len(unicodeDescription.split(" ")) == \
						   unicodeDescriptionLength - 1:
							safe_print("Warning (non-critical): '%s' "
									   "Unicode part starts with UTF-16 big "
									   "endian BOM, but actual contents seem "
									   "to be UTF-16 little endian" % 
									   tagData[:4])
							# fix fubar'd desc
							unicodeDescription = unicode(
								"\0".join(unicodeDescription.split(" ")), 
								"utf-16-le", errors="replace")
						else:
							unicodeDescription = unicode(unicodeDescription, 
														 "utf-16-be", 
														 errors="replace")
					elif unicodeDescription[:2] == "\xff\xfe":
						# UTF-16 Little Endian
						if debug: safe_print("UTF-16 Little endian")
						unicodeDescription = unicodeDescription[2:]
						if unicodeDescription[0] == "\0":
							safe_print("Warning (non-critical): '%s' "
									   "Unicode part starts with UTF-16 "
									   "little endian BOM, but actual "
									   "contents seem to be UTF-16 big "
									   "endian" % tagData[:4])
							# fix fubar'd desc
							unicodeDescription = unicode(unicodeDescription, 
														 "utf-16-be", 
														 errors="replace")
						else:
							unicodeDescription = unicode(unicodeDescription, 
														 "utf-16-le", 
														 errors="replace")
					else:
						if debug: safe_print("ASSUMED UTF-16 Big Endian")
						unicodeDescription = unicode(unicodeDescription, 
													 "utf-16-be", 
													 errors="replace")
				unicodeDescription = unicodeDescription.strip("\0\n\r ")
				if unicodeDescription:
					if unicodeDescription.find("\0") < 0:
						self.Unicode = unicodeDescription
					else:
						safe_print("Error (non-critical): could not decode "
								   "'%s' Unicode part - null byte(s) "
								   "encountered" % tagData[:4])
			except UnicodeDecodeError:
				safe_print("UnicodeDecodeError (non-critical): could not "
						   "decode '%s' Unicode part" % tagData[:4])
		else:
			charBytes = 1
		macOffset = unicodeOffset + 8 + unicodeDescriptionLength * charBytes
		macOffsetBackup = macOffset
		if tagData[macOffset:macOffset + 5] == "\0\0\0\0\0":
			macOffset += 5	# fix for fubar'd desc
		self.macScriptCode = 0
		if len(tagData) > macOffset + 2:
			self.macScriptCode = uInt16Number(tagData[macOffset:macOffset + 2])
			macDescriptionLength = ord(tagData[macOffset + 2])
			if macDescriptionLength:
				if macOffsetBackup < macOffset:
					safe_print("Warning (non-critical): '%s' Macintosh "
							   "part offset points to null bytes" % 
							   tagData[:4])
				try:
					macDescription = unicode(tagData[macOffset + 3:macOffset + 
											 3 + macDescriptionLength], 
											 "mac-" + 
											 encodings["mac"][self.macScriptCode], 
											 errors="replace").strip("\0\n\r ")
					if macDescription:
						self.Macintosh = macDescription
				except UnicodeDecodeError:
					safe_print("UnicodeDecodeError (non-critical): could not "
							   "decode '%s' Macintosh part" % tagData[:4])
	
	@Property
	def tagData():
		doc = """
		Return raw tag data.
		"""
	
		def fget(self):
			tagData = ["desc", "\0" * 4,
					   uInt32Number_tohex(len(self.ASCII) + 1),	 # count of ASCII chars + 1
					   self.ASCII + "\0",  # ASCII desc, \0 terminated
					   uInt32Number_tohex(self.get("unicodeLanguageCode", 0))]
			if "Unicode" in self:
				tagData.extend([uInt32Number_tohex(len(self.Unicode) + 2),	# count of Unicode chars + 2 (1 char = 2 byte)
								"\xfe\xff" + self.Unicode.encode("utf-16-be", "replace") + 
								"\0\0"])  # Unicode desc, \0\0 terminated
			else:
				tagData.append(uInt32Number_tohex(0))  # Unicode desc length = 0
			tagData.append(uInt16Number_tohex(self.get("macScriptCode", 0)))
			if "Macintosh" in self:
				macDescription = self.Macintosh[:66]
				tagData.extend([uInt8Number_tohex(len(macDescription) + 1),	 # count of Macintosh chars + 1
								macDescription.encode("mac-" + 
													  encodings["mac"][self.get("macScriptCode", 0)], 
													  "replace") + "\0"])
			else:
				tagData.extend([uInt32Number_tohex(0),	# Mac desc length = 0
								"\0" * 67])
			return "".join(tagData)
		
		def fset(self, tagData):
			pass
		
		return locals()

	def __str__(self):
		return unicode(self).encode(sys.getdefaultencoding())

	def __unicode__(self):
		if sys.platform == "darwin":
			localizedTypes = ("Unicode", "Macintosh", "ASCII")
		else:
			localizedTypes = ("Unicode", "ASCII", "Macintosh")
		for localizedType in localizedTypes:
			if localizedType in self:
				value = self[localizedType]
				if not isinstance(value, unicode):
					# Even ASCII description may contain non-ASCII chars, so 
					# assume system encoding and convert to unicode, replacing 
					# unknown chars
					value = unicode(value, fs_enc, errors="replace")
				return value


def TextType(tagData, tagSignature):
	tag = Text(tagData[8:].rstrip("\0"))
	tag.tagData = tagData
	tag.tagSignature = tagSignature
	return tag


class VideoCardGammaType(ICCProfileTag, ADict):

	# Private tag
	# http://developer.apple.com/documentation/GraphicsImaging/Reference/ColorSync_Manager/Reference/reference.html#//apple_ref/doc/uid/TP30000259-CH3g-C001473

	def __init__(self, tagData, tagSignature):
		ICCProfileTag.__init__(self, tagData, tagSignature)

	def printNormalizedValues(self, amount=None, digits=12):
		"""
		Normalizes and prints all values in the vcgt (range of 0.0...1.0).
		
		For a 256-entry table with linear values from 0 to 65535:
		#	REF			   C1			  C2			 C3
		001 0.000000000000 0.000000000000 0.000000000000 0.000000000000
		002 0.003921568627 0.003921568627 0.003921568627 0.003921568627
		003 0.007843137255 0.007843137255 0.007843137255 0.007843137255
		...
		You can also specify the amount of values to print (where a value 
		lesser than the entry count will leave out intermediate values) 
		and the number of digits.
		
		"""
		if amount is None:
			if hasattr(self, 'entryCount'):
				amount = self.entryCount
			else:
				amount = 256  # common value
		values = self.getNormalizedValues(amount)
		entryCount = len(values)
		channels = len(values[0])
		header = ['REF']
		for k in xrange(channels):
			header.append('C' + str(k + 1))
		header = [title.ljust(digits + 2) for title in header]
		safe_print("#".ljust(len(str(amount)) + 1) + " ".join(header))
		for i, value in enumerate(values):
			formatted_values = [str(round(channel, 
								digits)).ljust(digits + 2, '0') for 
					  channel in value]
			safe_print(str(i + 1).rjust(len(str(amount)), '0'), 
					   str(round(i / float(entryCount - 1), 
								 digits)).ljust(digits + 2, '0'), 
					   " ".join(formatted_values))


class VideoCardGammaFormulaType(VideoCardGammaType):

	def __init__(self, tagData, tagSignature):
		VideoCardGammaType.__init__(self, tagData, tagSignature)
		data = tagData[12:]
		self.update({
			"redGamma": u16Fixed16Number(data[0:4]),
			"redMin": u16Fixed16Number(data[4:8]),
			"redMax": u16Fixed16Number(data[8:12]),
			"greenGamma": u16Fixed16Number(data[12:16]),
			"greenMin": u16Fixed16Number(data[16:20]),
			"greenMax": u16Fixed16Number(data[20:24]),
			"blueGamma": u16Fixed16Number(data[24:28]),
			"blueMin": u16Fixed16Number(data[28:32]),
			"blueMax": u16Fixed16Number(data[32:36])
		})
	
	def getNormalizedValues(self, amount=None):
		if amount is None:
			amount = 256  # common value
		step = 1.0 / float(amount - 1)
		rgb = AODict([("red", []), ("green", []), ("blue", [])])
		for i in xrange(0, amount):
			for key in rgb:
				rgb[key] += [float(self[key + "Min"]) + math.pow(step * i / 1.0, 
								float(self[key + "Gamma"])) * 
							 float(self[key + "Max"] - self[key + "Min"])]
		return zip(*rgb.values())
	
	def getTableType(self, entryCount=256, entrySize=2):
		"""
		Return gamma as table type.
		"""
		maxValue = math.pow(256, entrySize) - 1
		tagData = [self.tagData[:8], 
				   uInt32Number_tohex(0),  # type 0 = table
				   uInt16Number_tohex(3),  # channels
				   uInt16Number_tohex(entryCount),
				   uInt16Number_tohex(entrySize)]
		int2hex = {
			1: uInt8Number_tohex,
			2: uInt16Number_tohex,
			4: uInt32Number_tohex,
			8: uInt64Number_tohex
		}
		for key in ("red", "green", "blue"):
			for i in xrange(0, entryCount):
				vmin = float(self[key + "Min"])
				vmax = float(self[key + "Max"])
				gamma = float(self[key + "Gamma"])
				v = (vmin + 
					 math.pow(1.0 / (entryCount - 1) * i, gamma) * 
					 float(vmax - vmin))
				tagData.append(int2hex[entrySize](round(v * maxValue)))
		return VideoCardGammaTableType("".join(tagData), self.tagSignature)


class VideoCardGammaTableType(VideoCardGammaType):

	def __init__(self, tagData, tagSignature):
		VideoCardGammaType.__init__(self, tagData, tagSignature)
		if not tagData:
			self.update({"channels": 0,
						 "entryCount": 0,
						 "entrySize": 0,
						 "data": []})
			return
		data = tagData[12:]
		channels   = uInt16Number(data[0:2])
		entryCount = uInt16Number(data[2:4])
		entrySize  = uInt16Number(data[4:6])
		self.update({
			"channels": channels,
			"entryCount": entryCount,
			"entrySize": entrySize,
			"data": []
		})
		hex2int = {
			1: uInt8Number,
			2: uInt16Number,
			4: uInt32Number,
			8: uInt64Number
		}
		i = 0
		while i < channels:
			self.data.append([])
			j = 0
			while j < entryCount:
				index = 6 + i * entryCount * entrySize + j * entrySize
				self.data[i].append(hex2int[entrySize](data[index:index + 
															entrySize]))
				j = j + 1
			i = i + 1
	
	def getNormalizedValues(self, amount=None):
		if amount is None:
			amount = self.entryCount
		values = zip(*[[entry / 65535.0 for entry in channel] for channel in self.data])
		if amount <= self.entryCount:
			step = self.entryCount / float(amount - 1)
			all = values
			values = []
			for i, value in enumerate(all):
				if i == 0 or (i + 1) % step < 1 or i + 1 == self.entryCount:
					values += [value]
		return values
	
	def getFormulaType(self):
		"""
		Return formula representing gamma value at 50% input.
		"""
		maxValue = math.pow(256, self.entrySize) - 1
		tagData = [self.tagData[:8], 
				   uInt32Number_tohex(1)]  # type 1 = formula
		for channel in self.data:
			l = (len(channel) - 1) / 2.0
			floor = float(channel[int(math.floor(l))])
			ceil = float(channel[int(math.ceil(l))])
			vmin = channel[0] / maxValue
			vmax = channel[-1] / maxValue
			v = (vmin + ((floor + ceil) / 2.0) * (vmax - vmin)) / maxValue
			gamma = (math.log(v) / math.log(.5))
			print vmin, gamma, vmax
			tagData.append(u16Fixed16Number_tohex(gamma))
			tagData.append(u16Fixed16Number_tohex(vmin))
			tagData.append(u16Fixed16Number_tohex(vmax))
		return VideoCardGammaFormulaType("".join(tagData), self.tagSignature)
	
	def resize(self, length=128):
		data = [[], [], []]
		for i, channel in enumerate(self.data):
			for j in xrange(0, length):
				j *= (len(channel) - 1) / float(length - 1)
				if int(j) != j:
					floor = channel[int(math.floor(j))]
					ceil = channel[min(int(math.ceil(j)), len(channel) - 1)]
					interpolated = xrange(floor, ceil + 1)
					fraction = j - int(j)
					index = int(round(fraction * (ceil - floor)))
					v = interpolated[index]
				else:
					v = channel[int(j)]
				data[i].append(v)
		self.data = data
		self.entryCount = len(data[0])
	
	def resized(self, length=128):
		resized = self.__class__(self.tagData, self.tagSignature)
		resized.resize(length)
		return resized
	
	def smooth_cr(self, length=64):
		"""
		Smooth video LUT curves (Catmull-Rom).
		"""
		resized = self.resized(length)
		for i in xrange(0, len(self.data)):
			step = float(length - 1) / (len(self.data[i]) - 1)
			interpolation = CRInterpolation(resized.data[i])
			for j in xrange(0, len(self.data[i])):
				self.data[i][j] = int(round(interpolation(j * step)))
	
	def smooth_avg(self, passes=1, window=None):
		"""
		Smooth video LUT curves (moving average).
		
		passses	  Number of passes
		window	  Tuple or list containing weighting factors. Its length
				  determines the size of the window to use.
				  Defaults to (1.0, 1.0, 1.0)
		
		"""
		if not window or len(window) < 3 or len(window) % 2 != 1:
			window = (1.0, 1.0, 1.0)
		for x in xrange(0, passes):
			data = [[], [], []]
			for i, channel in enumerate(self.data):
				for j, v in enumerate(channel):
					tmpwindow = window
					while j > 0 and j < len(channel) - 1 and len(tmpwindow) >= 3:
						tl = (len(tmpwindow) - 1) / 2
						# print j, tl, tmpwindow
						if tl > 0 and j - tl >= 0 and j + tl <= len(channel) - 1:
							windowslice = channel[j - tl:j + tl + 1]
							windowsize = 0
							for k, weight in enumerate(tmpwindow):
								windowsize += float(weight) * windowslice[k]
							v = int(round(windowsize / sum(tmpwindow)))
							break
						else:
							tmpwindow = tmpwindow[1:-1]
					data[i].append(v)
			self.data = data
			self.entryCount = len(data[0])
	
	@Property
	def tagData():
		doc = """
		Return raw tag data.
		"""
	
		def fget(self):
			tagData = ["vcgt", "\0" * 4,
					   uInt32Number_tohex(0),  # type 0 = table
					   uInt16Number_tohex(len(self.data)),	# channels
					   uInt16Number_tohex(self.entryCount),
					   uInt16Number_tohex(self.entrySize)]
			int2hex = {
				1: uInt8Number_tohex,
				2: uInt16Number_tohex,
				4: uInt32Number_tohex,
				8: uInt64Number_tohex
			}
			for channel in self.data:
				for i in xrange(0, self.entryCount):
					tagData.append(int2hex[self.entrySize](channel[i]))
			return "".join(tagData)
		
		def fset(self, tagData):
			pass
		
		return locals()


class ViewingConditionsType(ICCProfileTag, ADict):

	def __init__(self, tagData, tagSignature):
		ICCProfileTag.__init__(self, tagData, tagSignature)
		self.update({
			"illuminant": XYZNumber(tagData[8:20]),
			"surround": XYZNumber(tagData[20:32]),
			"illuminantType": Illuminant(tagData[32:36])
		})


class XYZNumber(AODict):

	"""
	Byte
	Offset Content Encoded as...
	0..3   CIE X   s15Fixed16Number
	4..7   CIE Y   s15Fixed16Number
	8..11  CIE Z   s15Fixed16Number
	"""

	def __init__(self, binaryString):
		AODict.__init__(self)
		self.X, self.Y, self.Z = [s15Fixed16Number(chunk) for chunk in 
								  (binaryString[:4], binaryString[4:8], 
								   binaryString[8:12])]


class XYZType(ICCProfileTag, XYZNumber):

	def __init__(self, tagData, tagSignature):
		ICCProfileTag.__init__(self, tagData, tagSignature)
		XYZNumber.__init__(self, tagData[8:20])


class chromaticAdaptionTag(s15Fixed16ArrayType):
	
	def __init__(self, tagData, tagSignature):
		ICCProfileTag.__init__(self, tagData, tagSignature)
		data = self.tagData[8:]
		while data:
			if len(self) == 0 or len(self[-1]) == 3:
				self.append([])
			self[-1].append(s15Fixed16Number(data[0:4]))
			data = data[4:]


tagSignature2Tag = {
	"chad": chromaticAdaptionTag
}

typeSignature2Type = {
	"chrm": ChromacityType,
	"curv": CurveType,
	"desc": TextDescriptionType,  # ICC v2
	"dtim": DateTimeType,
	"meas": MeasurementType,
	"mluc": MultiLocalizedUnicodeType,	# ICC v4
	"sf32": s15Fixed16ArrayType,
	"sig ": SignatureType,
	"text": TextType,
	"vcgt": videoCardGamma,
	"view": ViewingConditionsType,
	"XYZ ": XYZType
}


class ICCProfileInvalidError(IOError):

	def __str__(self):
		return self.args[0]


class ICCProfile:

	"""
	Returns a new ICCProfile object. 
	
	Optionally initialized with a string containing binary profile data or 
	a filename, or a file-like object. Also if the 'load' keyword argument
	is False (default True), only the header will be read initially and
	loading of the tags will be deferred to when they are accessed the
	first time.
	
	"""

	def __init__(self, profile=None, load=True):
		self.ID = "\0" * 16
		self._data = None
		self._file = None
		self._tags = AODict()
		self.fileName = None
		self.is_loaded = False
		self.size = 0
		
		if profile:
		
			data = None
			
			if type(profile) in (str, unicode):
				if profile.find("\0") < 0:
					# filename
					if not os.path.isfile(profile) and \
					   not os.path.sep in profile and \
					   not os.path.altsep in profile:
						for path in iccprofiles_home + filter(lambda x: 
							x not in iccprofiles_home, iccprofiles):
							if os.path.isdir(path):
								for path, dirs, files in os.walk(path):
									path = os.path.join(path, profile)
									if os.path.isfile(path):
										profile = path
										break
								if os.path.isfile(path):
									break
					profile = open(profile, "rb")
				else: # binary string
					data = profile
					self.is_loaded = True
			if not data: # file object
				self._file = profile
				self.fileName = self._file.name
				self._file.seek(0)
				data = self._file.read(128)
				self.close()
			
			if not data or len(data) < 128:
				raise ICCProfileInvalidError("Not enough data")
			
			if data[36:40] != "acsp":
				raise ICCProfileInvalidError("Profile signature mismatch - "
											 "expected 'acsp', found '" + 
											 data[36:40] + "'")
			
			header = data[:128]
			self.size = uInt32Number(header[0:4])
			self.preferredCMM = header[4:8].strip("\0\n\r ")
			self.version = float(str(ord(header[8:12][0])) + "." + 
								   str(ord(header[8:12][1])))
			self.profileClass = header[12:16].strip()
			self.colorSpace = header[16:20].strip()
			self.connectionColorSpace = header[20:24].strip()
			self.dateTime = dateTimeNumber(header[24:36])
			self.platform = header[40:44].strip("\0\n\r ")
			flags = uInt16Number(header[44:48][:2])
			self.embedded = flags | 1 == flags
			self.independent = flags | 2 != flags
			deviceAttributes = uInt32Number(header[56:64][:4])
			self.device = {
				"manufacturer": header[48:52].strip("\0\n\r "),
				"model": header[52:56].strip("\0\n\r "),
				"attributes": {
					"reflective":	deviceAttributes | 1 != deviceAttributes,
					"glossy":		deviceAttributes | 2 != deviceAttributes,
					"positive":		deviceAttributes | 4 != deviceAttributes,
					"color":		deviceAttributes | 8 != deviceAttributes
				}
			}
			self.intent = uInt32Number(header[64:68])
			self.illuminant = XYZNumber(header[68:80])
			self.creator = header[80:84].strip("\0\n\r ")
			if header[84:100] != "\0" * 16:
				self.ID = header[84:100]
			
			self._data = data[:self.size]
			
			if load:
				self.tags
	
	def __del__(self):
		self.close()
	
	@property
	def data(self):
		"""
		Get raw binary profile data.
		
		This will re-assemble the various profile parts (header, 
		tag table and data) on-the-fly.
		
		"""
		# Assemble tag table and tag data
		tagCount = len(self.tags)
		if not self._data or len(self._data) < 128:
			return None
		tagTable = []
		tagTableSize = tagCount * 12
		tagsData = []
		tagsDataOffset = []
		tagDataOffset = 128 + 4 + tagTableSize
		for tagSignature in self.tags:
			tagData = self.tags[tagSignature].tagData
			tagDataSize = len(tagData)
			# Pad all data with binary zeros so it lies on 4-byte boundaries
			padding = int(math.ceil(tagDataSize / 4.0)) * 4 - tagDataSize
			tagData += "\0" * padding
			tagTable.append(tagSignature)
			if tagData in tagsData:
				tagTable.append(uInt32Number_tohex(tagsDataOffset[tagsData.index(tagData)]))
			else:
				tagTable.append(uInt32Number_tohex(tagDataOffset))
			tagTable.append(uInt32Number_tohex(tagDataSize))
			if not tagData in tagsData:
				tagsData.append(tagData)
				tagsDataOffset.append(tagDataOffset)
				tagDataOffset += tagDataSize + padding
		header = uInt32Number_tohex(128 + 4 + tagTableSize + 
									len("".join(tagsData))) + self._data[4:84] + self.ID + self._data[100:128]
		data = "".join([header, uInt32Number_tohex(tagCount), 
						"".join(tagTable), "".join(tagsData)])
		return data
	
	@property
	def tags(self):
		"""
		Profile Tag Table.
		
		See also: http://www.sno.phy.queensu.ca/~phil/exiftool/TagNames/ICC_Profile.html
		
		"""
		if not self._tags:
			self.load()
			if self._data and len(self._data) > 131:
				# tag table and tagged element data
				tagCount = uInt32Number(self._data[128:132])
				if debug: print "tagCount:", tagCount
				tagTable = self._data[132:132 + tagCount * 12]
				discard_len = 0
				tags = {}
				while tagTable:
					tag = tagTable[:12]
					if len(tag) < 12:
						raise ICCProfileInvalidError("Tag table is truncated")
					tagSignature = tag[:4]
					if debug: print "tagSignature:", tagSignature
					tagDataOffset = uInt32Number(tag[4:8])
					if debug: print "	 tagDataOffset:", tagDataOffset
					tagDataSize = uInt32Number(tag[8:12])
					if debug: print "	 tagDataSize:", tagDataSize
					if tagSignature in self._tags:
						safe_print("Error (non-critical): Tag '%s' already "
								   "encountered. Skipping..." % tagSignature)
					else:
						if (tagDataOffset, tagDataSize) in tags:
							if debug: print "	 tagDataOffset and tagDataSize indicate shared tag"
							self._tags[tagSignature] = tags[(tagDataOffset, tagDataSize)]
						else:
							start = tagDataOffset - discard_len
							if debug: print "	 tagData start:", start
							end = tagDataOffset - discard_len + tagDataSize
							if debug: print "	 tagData end:", end
							tagData = self._data[start:end]
							if len(tagData) < tagDataSize:
								raise ICCProfileInvalidError("Tag data for tag %r (offet %i, size %i) is truncated" % (tagSignature,
																													   tagDataOffset,
																													   tagDataSize))
							##self._data = self._data[:128] + self._data[end:]
							##discard_len += tagDataOffset - 128 - discard_len + tagDataSize
							##if debug: print "	   discard_len:", discard_len
							typeSignature = tagData[:4]
							if len(typeSignature) < 4:
								raise ICCProfileInvalidError("Tag type signature for tag %r (offet %i, size %i) is truncated" % (tagSignature,
																																 tagDataOffset,
																																 tagDataSize))
							if debug: print "	 typeSignature:", typeSignature
							try:
								if tagSignature in tagSignature2Tag:
									tag = tagSignature2Tag[tagSignature](tagData, tagSignature)
								elif typeSignature in typeSignature2Type:
									tag = typeSignature2Type[typeSignature](tagData, tagSignature)
								else:
									tag = ICCProfileTag(tagData, tagSignature)
							except Exception, exception:
								raise ICCProfileInvalidError("Couldn't parse tag %r (type %r, offet %i, size %i): %s" % (tagSignature,
																														 typeSignature,
																														 tagDataOffset,
																														 tagDataSize,
																														 exception))
							self._tags[tagSignature] = tags[(tagDataOffset, tagDataSize)] = tag
					tagTable = tagTable[12:]
				self._data = self._data[:128]
		return self._tags
	
	def calculateID(self):
		"""
		Calculates, sets, and returns the profile's ID (checksum).
		
		Calling this function always recalculates the checksum on-the-fly, 
		in contrast to just accessing the ID property.
		
		The entire profile, based on the size field in the header, is used 
		to calculate the ID after the values in the Profile Flags field 
		(bytes 44 to 47), Rendering Intent field (bytes 64 to 67) and 
		Profile ID field (bytes 84 to 99) in the profile header have been 
		temporarily replaced with zeros.
		
		"""
		data = self.data[:44] + "\0\0\0\0" + self.data[48:64] + "\0\0\0\0" + \
			   self.data[68:84] + "\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0" + \
			   self.data[100:]
		self.ID = md5(data).digest()
		return self.ID
	
	def close(self):
		"""
		Closes the associated file object (if any).
		"""
		if self._file and not self._file.closed:
			self._file.close()
	
	def getCopyright(self):
		"""
		Return profile copyright.
		"""
		return unicode(self.tags.get("cprt", ""))
	
	def getDescription(self):
		"""
		Return profile description.
		"""
		return unicode(self.tags.get("desc", ""))
	
	def getDeviceManufacturerDescription(self):
		"""
		Return device manufacturer description.
		"""
		return unicode(self.tags.get("dmnd", ""))
	
	def getDeviceModelDescription(self):
		"""
		Return device model description.
		"""
		return unicode(self.tags.get("dmdd", ""))
	
	def getViewingConditionsDescription(self):
		"""
		Return viewing conditions description.
		"""
		return unicode(self.tags.get("vued", ""))
	
	def getTechnologySummary(self):
		"""
		Return description of the device the profile represents.
		N.B. make this a real tag.
		"""
		return unicode(technology.get(self.tags.get("tech", ""), ""))
	
	def getViewTargetIlluminant(self):
		"""
		Return target viewing illuminant.
		"""
		if self.tags.get("view", ""):
			if self.tags['view'].get("illuminantType", ""):
				if self.tags['view']['illuminantType'].get("description", ""):
					return unicode(self.tags['view']['illuminantType'].get("description", ""))
		return u""
	
	def getMeasuredIlluminant(self):
		"""
		Return illuminant recorded at the profiles' source.
		"""
		if self.tags.get("meas", ""):
			if self.tags['meas'].get("illuminantType", ""):
				if self.tags['meas']['illuminantType'].get("description", ""):
					return unicode(self.tags['meas']['illuminantType'].get("description", ""))
		return u""

		
	
	def getIDString(self):
		"""
		Return Base64-encoded profile ID.
		"""
		return base64.b64encode(self.calculateID())
	
	
	def isSame(self, profile, force_calculation=False):
		"""
		Compare the ID of profiles.
		
		Returns a boolean indicating if the profiles have the same ID.
		
		profile can be a ICCProfile instance, a binary string
		containing profile data, a filename or a file object.
		
		"""
		if not isinstance(profile, self.__class__):
			profile = self.__class__(profile)
		if force_calculation or self.ID == "\0" * 16:
			self.calculateID()
		if force_calculation or profile.ID == "\0" * 16:
			profile.calculateID()
		return self.ID == profile.ID
	
	def load(self):
		"""
		Loads the profile from the file object.

		Normally, you don't need to call this method, since the ICCProfile 
		class automatically loads the profile when necessary (load does 
		nothing if the profile was passed in as a binary string).
		
		"""
		if not self.is_loaded and self._file:
			if self._file.closed:
				self._file = open(self._file.name, "rb")
				self._file.seek(len(self._data))
			self._data += self._file.read(self.size - len(self._data))
			self._file.close()
			self.is_loaded = True
	
	def read(self, profile):
		"""
		Read profile from binary string, filename or file object.
		Same as self.__init__(profile)
		"""
		self.__init__(profile)
	
	def write(self, stream_or_filename=None):
		"""
		Write profile to stream.
		
		This will re-assemble the various profile parts (header, 
		tag table and data) on-the-fly.
		
		"""
		if not stream_or_filename:
			if self._file:
				if not self._file.closed:
					self.close()
				stream_or_filename = self.fileName
		if isinstance(stream_or_filename, basestring):
			stream = open(stream_or_filename, "wb")
		else:
			stream = stream_or_filename
		stream.write(self.data)
		if isinstance(stream_or_filename, basestring):
			stream.close()
	
	def __repr__(self):
		if self.data:
			return str(self.data)
		return ''
	
	def __str__(self):
		return "<ICCProfile: %s - %s>" % (self.getDescription(), self.getCopyright())
	
	def __unicode__(self):
		if self.data:
			return str(self.data)
		return ''
	
	def __eq__(self, other):
		return self.isSame(other)
	
	def __ne__(self, other):
		return not self.isSame(other)
	
