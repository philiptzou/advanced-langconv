#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup, Extension

converter = Extension('langconv.converter', sources = ['langconv/converter.c'])

setup(
	name = 'AdvancedLangConv',
	version = '0.01',
	description = 'Advanced Language Converter',
	url = 'http://code.google.com/p/advanced-langconv/',
	packages = ['langconv'],
	ext_modules = [converter]
) 
