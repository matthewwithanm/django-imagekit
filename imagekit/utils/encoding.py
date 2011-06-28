#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
encoding.py

From the excellent DispCalGUI by Florian Höch:

    http://dispcalgui.hoech.net/

Copyright (c) 2011 OST, LLC. 
"""
from encodings.aliases import aliases
import locale
import sys

if hasattr(sys.stdout, 'isatty'):
	if sys.stdout.isatty():
		if sys.platform == "win32":
			try:
				from win32console import GetConsoleCP, GetConsoleOutputCP
			except ImportError:
				pass


def get_encoding(stream):
	""" Return stream encoding. """
	enc = None
	if stream in (sys.stdin, sys.stdout, sys.stderr):
		if sys.platform == "darwin":
			# There is no way to determine it reliably under OS X 10.4?
			return "UTF-8"
		elif sys.platform == "win32":
			if sys.version_info >= (2, 6):
				# Windows/Python 2.6+: If a locale is set, the actual encoding 
				# of stdio changes, but the encoding attribute isn't updated
				enc = locale.getlocale()[1]
			if not enc:
				try:
					if stream is (sys.stdin):
						enc = aliases.get(str(GetConsoleCP()))
					else:
						enc = aliases.get(str(GetConsoleOutputCP()))
				except:
					pass
	enc = enc or getattr(stream, "encoding", None) or \
		  locale.getpreferredencoding() or sys.getdefaultencoding()
	return enc


def get_encodings():
	""" Return console encoding, filesystem encoding. """
	enc = get_encoding(sys.stdout)
	fs_enc = sys.getfilesystemencoding() or enc
	return enc, fs_enc
