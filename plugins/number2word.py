#!/usr/bin/env python3

"""digits into words

Convert the numbers into words.
"""

__version__  = 0.1
__authors__  = 'rho'
__support__  = 'https://github.com/foss-np/anubad/'

import os

class num2word:
    def __init__(self, word_map, interval):
        self.word_map = word_map
        self.interval = interval
        self.word  = []


    def convert(self, query):
        self.word.clear()

        n = int(query)
        l = len(query)
        if   n > 999 : self.pow_interval(n, l)
        elif n > 99  : self.hundreds(n)
        else         : self.base(n)

        return self.word


    def high_order_names(self, n):
        for digit, word in self.word_map[100:]:
            if n != digit: continue
            return word
        return str(n)


    def base(self, n):
        w = self.word_map[n][1]
        print(w)
        self.word.append(w)
        return w


    def hundreds(self, n, l=2):
        r, m = divmod(n, 100)

        if r != 0: # when there is no tens places
            self.base(r)
            self.base(100)

        if m:
            if l == 2:
                self.word.append('and')
                print('and')

            self.base(m)


    def pow_interval(self, n, l):
        if n < 1000:
            return self.hundreds(n);

        if l > 3:
            shift = ((l -3) % self.interval)
        else:
            shift = l % 3 

        exp = l - shift
        place = 10**exp
        r, m = divmod(n, place)
        print("len(%d) - %d;"%(l, shift), "10**%d = %d:"%(exp, place), (r, m))

        if r != 0:
            self.hundreds(r, l)
            w = self.high_order_names(place)
            self.word.append(w)
            print("places:", w)

        if m:
            self.pow_interval(m, l-self.interval);


class adaptor:
    def __init__(self, liststore, src=''):
        self.src = src

        num_en = []
        num_ne = []
        for word, (ID, *has_hash_tag, parsed_info) in liststore.items():
            noun = ""
            for pos, val in parsed_info:
                if pos == 'noun' and noun == "":
                    if not val: continue
                    noun = val
                    continue
                if pos == '_num':
                    if not val: continue
                    if not val.isdigit(): continue
                    v = int(val)
                    num_en.append((v, word))
                    num_ne.append((v, noun))
                    continue

        num_en.sort()
        num_ne.sort()
        self.en = num2word(num_en, 3)
        self.ne = num2word(num_ne, 2)


    def gui_reflect(self, query):
        n = int(query)
        t = "".join(chr(int(d) + 2406) for d in query)

        parsed_info = (
            ('_transliterate', t),
            ("{:,}".format(n), ' '.join(self.en.convert(query))),
            ('unknown', ''),
            ('unknown', ' '.join(self.ne.convert(query))),
        )
        FULL = {(query, int(query), self.src): parsed_info}
        FUZZ = dict()
        return FULL, FUZZ


def plugin_main(app, fullpath):
    for gloss in app.cnf.glossary_list:
        if "foss" in gloss['name']:
            break
    else:
        return False

    path = os.path.expanduser(gloss['path'])
    gloss = app.home.core.Glossary.instances[path + 'en2ne/']
    liststore, ulta = gloss['numbers.tra']

    n2w = adaptor(liststore, path + 'numbers.tra')
    app.home.engines.append((lambda q: q.isdigit(), n2w.gui_reflect))


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

    n2w = adaptor(liststore, src)

    query = '०१२३४५६७८९1'
    n2w.en.convert(query)
    n2w.ne.convert('333000')


if __name__ == '__main__':
    main()
    import doctest
    doctest.testmod()
