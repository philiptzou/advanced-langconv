
# Constants
CACHE_FILE, CACHE_DATABASE, CACHE_MEMCACHE = xrange(3)

class Settings(object):
    def __init__(self, settings):
        self._settings = dict(
            # cache setting
            CACHEMETHOD = CACHE_FILE, # could be database or memcache

            # valid variants
            VALIDVARIANTS = ['zh-hans', 'zh-hant', 'zh-cn', 'zh-hk', 'zh-sg', 'zh-tw'],

            # variant =fallback on=> variants
            VARIANTFALLBACK = {
                'zh': ['zh-hans', 'zh-hant', 'zh-cn', 'zh-hk', 'zh-sg', 'zh-hk'],
                'zh-hans': [],
                'zh-cn': ['zh-hans','zh-sg'],
                'zh-sg': ['zh-hans','zh-cn'],
                'zh-hant': [],
                'zh-tw': ['zh-hant','zh-hk'],
                'zh-hk': ['zh-hant','zh-tw']
            },
        )
        self._settings.update(settings)
    
    def __getattr__(self, name):
        try:
            return self._settings[name]
        except KeyError:
            raise AttributeError

