#!/usr/bin/env python3

"""digits into words

Convert the numbers into words.
"""

__version__  = 0.3
__authors__  = 'rho'
__support__  = 'https://github.com/foss-np/anubad/'

import os

class num2word:
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


    def high_order_names(self, n):
        for digit, word in self.word_map[100:]:
            if n != digit: continue
            return word
        return str(n)


    def base(self, n):
        return self.word_map[n][1]


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
        # print("len(%d) - %d;"%(l, shift), "10**%d = %d:"%(exp, place), (r, m))

        if r != 0:
            self.hundreds(r, l)
            self.words.append(self.high_order_names(place))

        if m:
            self.pow_interval(m, l-self.interval);


class Adaptor(dict):
    SRC = 'number2word plugin'
    def __init__(self, liststore):
        super().__init__()
        self.engine = {
            'name'   : "number2word",
            'filter' : lambda q: q.isdigit(),
            'piston' : self.gui_reflect,
        }


        num_en = []
        num_ne = []
        for word, (ID, *has_hash_tag, parsed_info) in liststore.items():
            noun = ""
            for pos, val in parsed_info:
                if pos == 'noun' and noun == "":
                    if not val: continue
                    noun = val.split('/')[0]
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
        self.en = num2word(num_en, 3, False)
        self.ne = num2word(num_ne, 2, True, 2406)


    def gui_reflect(self, query):
        parsed_info = (
            self.en.convert(query),
            ('unknown', ''),
            self.ne.convert(query),
        )


        FULL = {(query, int(query), __class__.SRC): parsed_info}
        return { query: (FULL, dict()) }

def plugin_main(app, fullpath):
    for gloss in app.cnf.glossary_list:
        if "foss" in gloss['name']:
            break
    else:
        return False

    path = os.path.expanduser(gloss['path'])
    gloss = app.home.core.Glossary.instances[path + 'en2ne/']
    liststore, ulta = gloss['numbers.tra']

    n2w = Adaptor(liststore)
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

    n2w = Adaptor(liststore, src)

    print(n2w.en.convert('1'))
    print(n2w.en.convert('12'))
    print(n2w.en.convert('123'))
    print(n2w.en.convert('1234'))
    print(n2w.en.convert('12345'))
    print(n2w.en.convert('123456'))
    print(n2w.en.convert('1234567'))
    print(n2w.ne.convert('12345679'))
    print(n2w.ne.convert('123456790'))
    print(n2w.ne.convert('०१२३४५६७८९1'))


if __name__ == '__main__':
    main()
    import doctest
    doctest.testmod()
