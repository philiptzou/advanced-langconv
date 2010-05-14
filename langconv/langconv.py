"""
Advanced Language Converter
"""
from globalfunc import *
from settings import *
import re
if USINGC:
    import converter

class ConverterHandler(object):
    def __init__(self, variant):
    
        ### INITIATE CONVERTERS AND RULEPARSER ###
        self.variant = variant
        self.converters = {}
        self.ruleparser = _RuleParser(variant, self)
        
        for vvariant in VALIDVARIANTS:
            self.converters[vvariant] = _Converter(vvariant, self)
        
        self.mainconverter = self.converters[variant]

    def convert(self, content, parserule = True):
        return self.mainconverter.convert(content, parserule)

    def convert_to(self, variant, content, parserule = True):
        return self.converters[variant].convert(content, parserule)

    def parse(self, text):
        return self.ruleparser.parse(text)

class _Converter(object):
    def __init__(self, variant, handler):
        
        ### DEFINATION OF VARIBLES ###
        self.variant = variant # The variant we want convert to
        self.handler = handler
        self.convtable = {} # The conversion table
        self.quicktable = {} # A quick table
        self.maxlen = 0 # Max length of the words
        self.maxdepth = 10 # Depth for recursive convert rule
        self.hooks = {'depth_exceed_msg': None,
                     'rule_parser': None} # Hooks for converter
        
        ### DEFINATION OF LAMBDA METHOD ###
        self.get_message = lambda name, *args, **kwargs: get_message(variant, name, *args, **kwargs)
        
        ### INITIATE FUNCTIONS ###
        self.load_table() # Load default table
        self.set_default_hooks() # As it says
    
    """def get_message(self, name, *args, **kwargs):
        return get_message(self.variant, name, *args, **kwargs)"""
    
    def set_default_hooks(self):
        """As it says."""
        self.hooks['depth_exceed_msg'] = lambda depth: self.get_message('deptherr', depth)
        self.hooks['rule_parser'] = self.handler.ruleparser.parse
    
    def set_hook(self, name, callfunc):
        self.hooks[name] = callfunc

    def add_quick(self, ori):
        """Add item to quicktable."""
        orilen = len(ori)
        self.maxlen = orilen > self.maxlen and orilen or self.maxlen
        try:
            wordlens = self.quicktable[ori[0]]
        except KeyError, err:
            self.quicktable[ori[0]] = [orilen]
        else:
            wllen = len(wordlens)
            pos = wllen // 2
            while pos > -1 and pos < wllen + 1:
                if pos == 0: left = orilen + 1
                else: left = wordlens[pos - 1]
                if pos == wllen: right = orilen - 1
                else: right = wordlens[pos]
                #print left, orilen, right, pos
                if orilen == left or orilen == right:
                    break
                elif left > orilen and orilen > right:
                    wordlens.insert(pos, orilen)
                    break
                elif orilen > left:
                    pos -= pos // 2 or 1
                else: # right > orilen
                    pos += (wllen - pos) // 2 or 1
    
    def load_table(self, isgroup = False):
        """Load a conversion table.
           Raise ImportException if an import error happens."""
        newtable = __import__('langconv.defaulttables.%s' % \
                   self.variant.replace('-', '_'), fromlist = 'convtable').convtable
        self.convtable.update(newtable)
        
        # try to load quicktable from cache
        if not isgroup:
            self.quicktable = get_cache('%s-qtable' % self.variant)
            self.maxlen = get_cache('%s-maxlen' % self.variant)
            if self.quicktable is not None and self.maxlen is not None:
                return
            else:
                self.quicktable = {}
                self.maxlen = 0
        
        for (ori, dst) in newtable.iteritems():
            self.add_quick(ori)
        
        # try to dump quicktable to cache
        if not isgroup:
            set_cache('%s-qtable' % self.variant, self.quicktable)
            set_cache('%s-maxlen' % self.variant, self.maxlen)

    def update(self, newtable):
        self.convtable.update(newtable)
        for (ori, dst) in newtable.iteritems():
            self.add_quick(ori)
    
    def add_rule(self, ori, dst):
        """add a rule to convtable and quicktable"""
        self.convtable[ori] = dst
        self.add_quick(ori)
    
    def del_rule(self, ori, dst):
        if self.convtable.get(ori) == dst:
            self.convtable.pop(ori)
    
    if USINGC:
        def convert(self, content, parserules = True):
            content = to_unicode(content)
            return converter.convert(self, content, parserules)
    else:
        def recursive_convert_rule(self, content, pos, contlen, depth = 1):
            oripos = pos
            out = []
            exceedtime = 0
            while pos < contlen:
                token = content[pos:pos + 2]
                if token == '-{':
                    if depth < self.maxdepth:
                        inner, pos = self.recursive_convert_rule(content, pos + 2, contlen, depth + 1)
                        out.append(inner)
                        continue
                    else:
                        if not exceedtime and self.hooks['depth_exceed_msg'] is not None:
                            out.append(self.hooks['depth_exceed_msg'](depth))
                        exceedtime += 1
                elif token == '}-':
                    if depth >= self.maxdepth and exceedtime:
                        exceedtime -= 1
                    else:
                        inner = ''.join(out)
                        if not exceedtime:
                            inner = self.handler.parse(inner)
                        return (inner, pos + 2)
                out.append(content[pos])
                pos += 1
            else:
                # unclosed rule, won't parse but still auto convert
                return ('-', oripos - 1)
        
        def convert(self, content, parserules = True):
            """Use the specified variant to convert the content.
               
               content is the string to convert,
               set parserules to False if you don't want to parse rules."""
            
            content = to_unicode(content)
            out = []
            contlen = len(content)
            pos = 0
            trytime = 0 # for debug
            while pos < contlen:
                if parserules and content[pos:pos + 2] == '-{':
                    # markup found
                    inner, pos = self.recursive_convert_rule(content, pos + 2, contlen)
                    out.append(inner)
                    continue
                
                wordlens = self.quicktable.get(content[pos])
                single = content[pos]
                if wordlens is None:
                    trytime += 1 # for debug
                    out.append(single)
                    pos += 1
                else:
                    for wordlen in wordlens:
                        trytime += 1 # for debug
                        oriword = content[pos:pos + wordlen]
                        convword = self.convtable.get(oriword)
                        if convword is not None:
                            out.append(convword)
                            pos += wordlen
                            break
                    else:
                        trytime += 1 # for debug
                        out.append(single)
                        pos += 1
            print trytime # for debug
            return ''.join(out)

class _RuleParser(object):
    def __init__(self, variant, handler):
        self.variant = variant
        self.handler = handler
        self.flagdict = {'A': lambda flag, rule: self.add_rule(flag, rule, display = True),
                              # add a single rule to convtable and return the converted result
                              # -{FLAG|rule}-
                              # FLAG: A[[;NF]|[;NA:variant]]
                         
                         'D': self.describe_rule,
                              # describe the rule
                              # -{D|rule}-
                         
                         'G': self.add_group,
                              # add a lot rules from a group to convtable
                              # -{G|groupname}-
                         
                         'H': lambda flag, rule: self.add_rule(flag, rule, display = False),
                              # add a single rule to convtable
                              # -{FLAG|rule}-
                              # FLAG: H[[;NF]|[;NA:variant]]
                         
                         'R': self.display_raw,
                              # raw content
                              # -{R|content}-
                         
                         'T': self.set_title,
                              # set title
                              # -{FLAG|rule}-
                              # FLAG: T[[;NF]|[;NA:variant]]
                        
                         '-': self.remove_rule,
                              # remove rules from convtable
                              # -{-|rule}-
                        }
        self.variants = VALIDVARIANTS
        self.fallback = VARIANTFALLBACK
        
        self.asfallback = {}
        for var in self.variants:
            self.asfallback[var] = []
        for varright in self.variants:
            for varleft in self.fallback[varright]:
                self.asfallback[varleft].append(varright)
        
        self.myfallback = self.fallback[self.variant]

        varsep_pattern = ';\s*(?='
        for variant in self.variants:
            varsep_pattern += '%s\s*:|' % variant # zh-hans:xxx;zh-hant:yyy
            varsep_pattern += '[^;]*?=>\s*%s\s*:|' % variant # xxx=>zh-hans:yyy; xxx=>zh-hant:zzz
        varsep_pattern += '\s*$)'
        self.varsep = re.compile(varsep_pattern)


    def parse(self, text):
        flagrule = text.split(u'|', 1)
        if len(flagrule) == 1:
            # flag is empty, so just call the default rule parser
            return self.parse_rule(text, withtable = False)
        else:
            flag, rule = flagrule
            flag = flag.strip()
            rule = rule.strip()
            ruleparser = self.flagdict.get(flag[0])
            if ruleparser:
                # we got a valid flag, call the parser now
                return ruleparser(flag, rule)
            else:
                # perhaps it's a "fallback convert"
                return self.fb_convert(text, flag, rule)

    def parse_rule(self, rule, withtable = True, allowfallback = True,
                   notadd = []):
        """parse rule and get default output."""
        #TODO:
        #add flags:
        #           NOFALLBACK
        #           NOCONVERT
        
        table = {}
        for variant in self.variants:
            table[variant] = {}

        bidtable = {}
        unidtable = {}
        all = ''
        out = ''
        overrule = False
        
        rule = rule.replace(u'=&gt;', u'=>')

        choices = self.varsep.split(rule)

        for choice in choices:
            if choice == '':
                continue
            
            #first, we split [xxx=>]zh-hans:yyy to ([xxx=>]zh-hans, yyy)
            part = choice.split(u':', 1)
            
            # only 'yyy'
            if len(part) == 1:
                all = part[0]
                out = all # output
                continue
            
            variant = part[0].strip() # [xxx=>]zh-hans
            toword = part[1].strip() # yyy
            
            #then, we split xxx=>zh-hans to (xxx, zh-hans)
            unid = variant.split(u'=>', 1)
            
            if toword:
                # only 'zh-hans:xxx'
                if len(unid) == 1 and variant in self.variants:
                    if variant == self.variant:
                        out = toword
                        overrule = True
                    elif allowfallback and \
                         not overrule and \
                         variant in self.myfallback:
                        out = toword
                    if withtable:
                        bidtable[variant] = toword
                    
                # 'xxx=>zh-hans:yyy'
                elif len(unid) == 2:
                    variant = unid[1].strip() # zh-hans
                    if variant == self.variant:
                        out = toword
                        overrule = True
                    elif allowfallback and \
                         not overrule and \
                         variant in self.myfallback:
                        out = toword
                    if withtable:
                        fromword = unid[0].strip()
                        if not unidtable.has_key(variant):
                            unidtable[variant] = {}
                        if toword and variant in self.variants:
                            if variant not in notadd:
                                unidtable[variant][fromword] = toword
                            if allowfallback:
                                for fbv in self.asfallback[variant]:
                                    if fbv not in notadd:
                                        if not unidtable.has_key(fbv):
                                            unidtable[fbv] = {}
                                        if not unidtable[fbv].has_key(fromword):
                                            unidtable[fbv][fromword] = toword
                elif out == '':
                    out = choice
            elif out == '':
                out = choice
                
        if not withtable:
            return out
        
        ### ELSE
        
        # add 'xxx': 'xxx' to every variant
        if all:
            for variant in self.variants:
                table[variant][all] = all

        # parse bidtable, aka tables filled by 'zh-hans:xxx'
        for (variant, toword) in bidtable.iteritems():
            for fromword in bidtable.itervalues():
                if variant not in notadd:
                    table[variant][fromword] = toword
                if allowfallback:
                    for fbv in self.asfallback[variant]:
                        if not table[fbv].has_key(fromword) and \
                        fbv not in notadd:
                            table[fbv][fromword] = toword
        
        # parse unidtable, aka tables filled by 'xxx=>zh-hans:yyy'
        for variant in unidtable.iterkeys():
            table[variant].update(unidtable[variant])
        
        ### ENDIF
        
        return (out, table)

    def _parse_multiflag(self, flag):
        allowfallback = True
        notadd = []
        # a valid multiflag could be:
        #    (A|H|T|-)[[;NF]|[;NA:variant]]
        for fpart in flag.split(';'):
            fpart = fpart.strip()
            if fpart == 'NF': # no fallback
                allowfallback = False
            elif fpart.startswith('NA'): # not add
                napart = fpart.split(':', 1)
                if len(napart) == 2 and napart[0].strip() == 'NA' and \
                   napart[1].strip() in self.variants:
                    notadd.append(napart[1])
        return (allowfallback, notadd)

    def add_rule(self, flag, rule, display):
        af, na = self._parse_multiflag(flag)
        
        out, tables = self.parse_rule(rule, withtable = True, \
                                          allowfallback = af, \
                                          notadd = na)
        for (variant, table) in tables.iteritems():
            self.handler.converters[variant].update(table)
        if display:
            return out
        else:
            return u''

    def describe_rule(self, flag, rule):
        return rule

    def add_group(self, flag, rule):
        return ''

    def display_raw(self, flag, rule):
        return rule

    def set_title(self, flag, rule):
        af, na = self._parse_multiflag(flag)
        
        out = self.parse_rule(rule, withtable = False, \
                                   allowfallback = af, \
                                   notadd = na)
        return ''

    def remove_rule(self, flag, rule):
        af, na = self._parse_multiflag(flag)
        
        out, tables = self.parse_rule(rule, withtable = True, \
                                          allowfallback = af, \
                                          notadd = na)
        for (variant, table) in tables.iteritems():
            for oridst in table.iteritems():
                self.handler.converters[variant].del_rule(*oridst)
        return ''

    def fb_convert(self, text, flag, rule):
        return text
