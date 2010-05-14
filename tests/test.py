#!/usr/bin/env python

from __future__ import with_statement
from langconv import ConverterHandler
from langconv.settings import VALIDVARIANTS
from time import time
import codecs
from os import listdir
from os.path import join, exists
from traceback import print_exc

WRITEOUTPUT = False

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
        for var in VALIDVARIANTS:
            print
            print 'testing', var, '...',
            start = time()
            try:
                convhandler = ConverterHandler(var)
                outp = convhandler.convert(inp, parserules)
            except Exception:
                print 'error occurred.'
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
                else:
                    with codecs.open(join('cases', testn, 'output.' + var), 'w', 'utf-8') as f:
                        f.write(outp)

if __name__ == '__main__':
    test()
