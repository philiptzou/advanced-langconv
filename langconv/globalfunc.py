from settings import *
from messages import messages
import os
try:
    import chardet
except ImportError:
    chardet = None
try:
    import cPickle as pickle
except ImportError:
    import pickle

def to_unicode(content):
    if not isinstance(content, basestring):
        content = unicode(content)
    elif not isinstance(content, unicode):
        enc = chardet.detect(content)['encoding'] if chardet else 'utf8'
        content = content.decode(enc)
    return content

def get_message(lang, name, *args, **kwargs):
    if messages.has_key(lang):
        msglist = messages[lang]
    else:
        msglist = messages['en']
    msg = to_unicode(msglist[name])
    for i in range(1, len(args) + 1):
        msg = msg.replace('$%d' % i, to_unicode(args[i - 1]))
    for (key, val) in kwargs.iteritems():
        msg = msg.replace('$%s' % key, to_unicode(val))
    return msg

def _get_cache_name(name, version = None):
    if version is not None:
        return '%s_%s.cache' % (name.replace('-', '_'), version)
    else:
        return '%s_unknown_version.cache' % name.replace('-', '_')

def set_cache(settings, name, obj, version = None):
    name = _get_cache_name(name, version)
    if settings.CACHEMETHOD == CACHE_FILE:
        try:
            pickle.dump(obj, open('./cache/%s' % name, 'w'))
        except Exception:
            os.makedirs('./cache')
            try:
                pickle.dump(obj, open('./cache/%s' % name, 'w'))
            except Exception:
                pass
    elif settings.CACHEMETHOD == CACHE_DATABASE:
        pass
    elif settings.CACHEMETHOD == CACHE_MEMCACHE:
        pass

def get_cache(settings, name, version = None):
    name = _get_cache_name(name, version)
    if settings.CACHEMETHOD == CACHE_FILE:
        try:
            return pickle.load(open('./cache/%s' % name))
        except:
            return None
    elif settings.CACHEMETHOD == CACHE_DATABASE:
        pass
    elif settings.CACHEMETHOD == CACHE_MEMCACHE:
        pass
