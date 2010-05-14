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

# variant =fallback on=> variants
VARIANTFALLBACK = {'zh': ['zh-hans', 'zh-hant', 'zh-cn', 'zh-hk', 'zh-sg', 'zh-hk'],
                   'zh-hans': [],
                   'zh-cn': ['zh-hans','zh-sg'],
                   'zh-sg': ['zh-hans','zh-cn'],
                   'zh-hant': [],
                   'zh-tw': ['zh-hant','zh-hk'],
                   'zh-hk': ['zh-hant','zh-tw']
                  }

# using C extension
USINGC = True
