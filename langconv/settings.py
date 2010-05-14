# -*- coding: utf-8 -*-

# The decode encoding allowed
ENCODING = ('UTF-8', 'GBK', 'BIG5HKSCS')

# cache setting
FILE = 1
DATABASE = 2
MEMCACHE = 3
CACHEMETHOD = FILE # could be database or memcache

# valid variants
VALIDVARIANTS = ['zh-hans', 'zh-hant', 'zh-cn', 'zh-hk', 'zh-sg', 'zh-tw']

# variant fallbacks
VARIANTFALLBACK = {'zh': ['zh-hans', 'zh-hant', 'zh-cn', 'zh-hk', 'zh-sg', 'zh-hk'],
                   'zh-hans': ['zh-cn','zh-sg'],
                   'zh-cn': ['zh-sg','zh-hans'],
                   'zh-sg': ['zh-cn','zh-hans'],
                   'zh-hant': ['zh-tw','zh-hk'],
                   'zh-tw': ['zh-hk','zh-hant'],
                   'zh-hk': ['zh-tw','zh-hant']
                  }

# using C extension
USINGC = True
