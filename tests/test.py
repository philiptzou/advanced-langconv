#!/usr/bin/env python

from __future__ import with_statement
from langconv import ConverterHandler
from time import time
import codecs
from os import listdir
from os.path import join, exists
from traceback import print_exc

def test():
	for testn in listdir('cases'):
		if not exists(join('cases', testn, 'input')):
			continue
		print
		print '-' * 40
		print
		print 'Running test', testn, '...'
		with codecs.open(join('cases', testn, 'input'), 'r', 'utf-8') as f:
			inp = f.read()
		print 'input size:', len(inp)
		parserules = True
		for var in ('zh', 'zh-hans', 'zh-hant', 'zh-cn', 'zh-hk', 'zh-sg', 'zh-tw'):
			print
			print 'testing', var, '...',
			start = time()
			try:
				convhandler = ConverterHandler(var)
				outp = convhandler.convert(inp, parserules)
			except Exception:
				print 'exception occurred.'
				print_exc()
			else:
				print '%.3f sec.' % (time() - start)
				if exists(join('cases', testn, 'output.' + var)):
					print 'comparing converter\'s output with expected output ...'
					with codecs.open(join('cases', testn, 'output.' + var), 'r', 'utf-8') as f:
						cp = f.read()
					if cp == outp:
						print 'OK'
					else:
						print 'FAILED'

if __name__ == '__main__':
	test()
