#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup, Extension

converter = Extension('converter', sources = ['converter.c'])

setup (name = 'AdvancedLangConv', version = '0.01', description = 'Advanced Language Converter', ext_modules = [converter]) 
