#!/usr/bin/env python3

"""digits into words

Convert the numbers into words.
"""

__version__  = 0.3
__authors__  = 'rho'
__support__  = 'https://github.com/foss-np/anubad/'

import os, sys

fp3 = sys.stderr

class InWords:
    def __init__(self, word_map, interval, drop_and=True, offset=48):
        self.word_map = word_map
        self.interval = interval
        self.offset   = offset
        self.drop_and = drop_and
        self.words = [] # to be share across methods


    def convert(self, query):
        n = int(query)
        s = "".join(chr(int(d) + self.offset) for d in str(n))
        l = len(s)

        digit = s[-3:]
        for i, d in enumerate(reversed(s[:-3])):
            if i % self.interval == 0:
                digit = ',' + digit
            digit = d + digit

        self.words.clear()
        if   n > 999 : self.pow_interval(n, l)
        elif n > 99  : self.hundreds(n)
        else         : self.words.append(self.base(n))

        return digit, ' '.join(self.words)


    def base(self, n):
        word = self.word_map.get(n)
        if word: return word
        if n > 100: return str(n)

        r, m = divmod(n, 10)
        word = self.word_map.get(r*10) if r != 0 else ''
        if word is None:
            word  = self.word_map.get(r)
            word += self.word_map.get(10)

        if m:
            word += ' ' +  self.word_map.get(m, ' ')

        return word


    def hundreds(self, n, l=2):
        r, m = divmod(n, 100)

        if r != 0: # when there is no tens places
            self.words.append(self.base(r))
            self.words.append(self.base(100))

        if m:
            if l == 2 and not self.drop_and:
                self.words.append('and')
            self.words.append(self.base(m))



    def pow_interval(self, n, l):
        if n < 1000:
            return self.hundreds(n);

        shift = (l - 3) % self.interval if l > 3 else l % 3
        exp = l - shift
        place = 10**exp
        r, m = divmod(n, place)
        print("len(%d) - %d;"%(l, shift), "10**%d = %d:"%(exp, place), (r, m), file=fp3)

        if r != 0:
            self.hundreds(r, l)
            self.words.append(self.base(place))

        if m:
            self.pow_interval(m, l-self.interval);


class Adaptor(dict):
    SRC = 'number2word plugin'
    def __init__(self):
        super().__init__()
        map_en = dict()
        for line in open(__file__.replace('.py', '.map')):
            k, v = line.split(';')
            map_en[int(k)] = v.strip()

        self['en'] = InWords(map_en, 3, False)

        self.engine = {
            'name'   : "number2word",
            'filter' : lambda q: q.isdigit(),
            'piston' : self.gui_reflect,
        }


    def map_gen(self, liststore, key=False):
        mapping = dict()
        for word, (*a, parsed_info) in liststore.items():
            if 'num' not in parsed_info.keys(): continue
            k = int(parsed_info['num'][0])
            v = word if key else parsed_info['n1'][0].split('/')[0]
            mapping[k] = v

        return mapping


    def gui_reflect(self, query):
        parsed_info = dict()

        for lang, obj  in self.items():
            k, v = obj.convert(query)
            # print(lang, k, v)
            parsed_info[k] = [ v ]

        FULL = {(query, int(query), __class__.SRC): parsed_info}
        return { query: (FULL, dict()) }


def plugin_main(app, fullpath):
    n2w = Adaptor()
    for path, gloss in app.home.core.Glossary.instances.items():
        numb = gloss.get('numbers.tra')
        if numb is None: continue
        l1, l2 = path.split('/')[-2].split('2')
        liststore, ulta = numb
        if l1 == "en": lang, key = l2, False
        else: lang, key = l1, True
        offset = 48
        if    lang == "ne": offset = 2406
        elif  lang == "jp": offset = 65296

        mapping = n2w.map_gen(liststore, key)
        n2w[lang] = InWords(mapping, 2, True, offset)

    app.home.search_engines.append(n2w.engine)


def main():
    import sys
    sys.path.append(sys.path[0]+'/../src/')

    import setting
    cnf = setting.main()

    for gloss in cnf.glossary_list:
        if "foss" in gloss['name']:
            break
    else:
        return False

    path = os.path.expanduser(gloss['path'])

    import core
    gloss = core.Glossary(path + 'en2ne/')

    liststore, ulta = gloss['numbers.tra']
    src = gloss.fullpath + 'numbers.tra'

    n2w = Adaptor()

    print(n2w['en'].convert('1'))
    print(n2w['en'].convert('12'))
    print(n2w['en'].convert('123'))
    print(n2w['en'].convert('1234'))
    print(n2w['en'].convert('12345'))
    print(n2w['en'].convert('123456'))
    print(n2w['en'].convert('०१२३४५६७'))


if __name__ == '__main__':
    main()
    import doctest
    doctest.testmod()
