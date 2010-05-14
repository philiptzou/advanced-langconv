from settings import *
from messages import messages
import cPickle, os

def to_unicode(content):
    if not isinstance(content, basestring):
        return unicode(content)
    if not isinstance(content, unicode):
        for enc in ENCODING:
            try:
                return content.decode(enc)
            except UnicodeDecodeError, err:
                pass
        else:
            raise UnicodeDecodeError(*err)
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

def set_cache(name, obj, version = None):
    name = _get_cache_name(name, version)
    if CACHEMETHOD == FILE:
        try:
            cPickle.dump(obj, open('./cache/%s' % name, 'w'))
        except Exception:
            pass
    elif CACHEMETHOD == DATABASE:
        pass
    elif CACHEMETHOD == MEMCACHE:
        pass

def get_cache(name, version = None):
    name = _get_cache_name(name, version)
    if CACHEMETHOD == FILE:
        try:
            return cPickle.load(open('./cache/%s' % name))
        except:
            return None
    elif CACHEMETHOD == DATABASE:
        pass
    elif CACHEMETHOD == MEMCACHE:
        pass
