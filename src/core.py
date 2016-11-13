#!/usr/bin/env python3

import os, sys
import traceback
from collections import OrderedDict

fp3 = fp4 = sys.stderr

FILE_TYPES = ["tsl", "fun", "abb", "tra"]

def edit_distance(s1, s2):
    """
    >>> edit_distance('this is a test', 'wokka wokka!!!')
    14
    """
    if len(s1) < len(s2): s1, s2 = s2, s1
    if len(s2) == 0: return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


class Glossary(dict):
    instances = OrderedDict()
    hashtags = dict() # for auto-complete

    def __init__(self, path):
        super().__init__()
        self.counter = 0
        self.fullpath = os.path.expanduser(path)
        self.load_glossary(self.fullpath)
        print("glossary:", path, self.counter, file=sys.stderr)

        __class__.instances[self.fullpath] = self


    def load_glossary(self, path):
        if not os.path.isdir(path):
            print("error: invalid glossary path ", file=sys.stderr)
            raise NotADirectoryError("Can not find "+path)

        for _file in os.listdir(path):
            name, dot, ext = _file.rpartition('.')
            if ext not in FILE_TYPES: continue
            src = self.fullpath + _file
            count, *self[_file] = self.load_entries(src)
            self.counter += count
            print("loaded: *%s %5d"%(src[-40:], count), file=fp4)


    def load_entries(self, src):
        liststore = dict()
        invert = dict()

        try:
            data = open(src, encoding="UTF-8").read()
        except:
            print("error: in file", src, file=sys.stderr)
            return

        i = 0 # NOTE: if file is empty
        for i, line in enumerate(data.splitlines(), 1):
            try:
                word, defination = line.split('; ')
            except Exception as e:
                print("fatal:", e, file=sys.stderr)
                print("wrong format %s: %d"%(src, i), file=sys.stderr)
                e.meta_info = (src, i)
                raise

            try:
                parsed_info = self.format_parser(defination)
            except Exception as e:
                e.meta_info = (src, i)
                raise

            # generate inverted list
            for pos, vals in parsed_info.items():
                if pos    == "":
                    print(parsed_info, file=sys.stderr)
                    e = Exception("empty pos tag ")
                    e.meta_info = (src, i)
                    raise e

                if   pos == 't': pass
                elif not pos[-1].isdigit(): continue

                for v in vals:
                    ID, info = invert.get(v, (tuple(), {}))
                    info[pos] = info.get(pos, []) + [word]
                    invert[v] = (
                        ID + tuple([i]),
                        info
                    )

            duplicate = liststore.get(word)
            if duplicate:
                print("repeated entry:", word, file=sys.stderr)
                print("%s: %d == %d"%(src, i, duplicate[0]), file=sys.stderr)
                e = Exception('Repeated entries')
                e.meta_info = (src, i)
                raise e

            for tag in parsed_info['#'].keys():
                __class__.hashtags[tag] = __class__.hashtags.get(tag, 0) + 1

            liststore[word] = (i, parsed_info)

        return i, liststore, invert


    @staticmethod
    def format_parser(raw):
        """
        >>> Glossary.format_parser('[मस्टर्ड] n(रायोको साग), #vegetable') == \
            {\
                't' : ['मस्टर्ड'],\
                'n1' : ['रायोको साग'],\
                '#' : {'#vegetable' : ['']}\
            }
        True
        >>> Glossary.format_parser('[वीट्] n(गहूँ) #crop, wiki{Wheat}') == \
            {\
                't'    : ['वीट्'],\
                'n1'    : ['गहूँ'],\
                '#'    : {'#crop' : ['']},\
                'wiki' : ['Wheat']\
            } # TODO '@Wheat': ['n1']
        True
        >>> Glossary.format_parser('[शेल] n(शंख किरो #animal), n(छिल्का, खोल, बोक्रा)') == \
            {\
                't' : ['शेल'],\
                'n1' : ['शंख किरो'],\
                '#' : {'#animal' : ['n1']},\
                'n2' : ['छिल्का', 'खोल', 'बोक्रा']\
            }
        True
        >>> Glossary.format_parser('[हेल्‍लो] n(नमस्कार, नमस्ते ), v(स्वागत, अभिवादन,)') == \
            {\
                't': ['हेल्‍लो'],\
                'n1': ['नमस्कार', 'नमस्ते'],\
                'v1': ['स्वागत', 'अभिवादन'],\
                '#': {}\
            }
        True
        >>> Glossary.format_parser('मिश्रित ब्याज, आवधिक ब्याज #finance') == \
            {\
                'u1': ['मिश्रित ब्याज', 'आवधिक ब्याज'],\
                '#': { '#finance': [''] }\
            }
        True
        >>> Glossary.format_parser('n(<thin> तुवाँलो ~fog)') == \
            {\
                'n1': ['<thin> तुवाँलो ~fog'],\
                '#': {}\
            } # TODO '~': 'fog'
        True
        >>> Glossary.format_parser('योगदान, सहाय , सहायता, ,,') == \
            {\
                'u1': ['योगदान', 'सहाय', 'सहायता'],\
                '#': {}\
            }
        True
        >>> Glossary.format_parser('कर') == {'u1': ['कर'], '#': {}}
        True
        """

        counter  = dict()
        output   = dict()
        hashtag  = dict()
        operator = []

        pos  = ""
        buff = ""
        ishashtag = False

        def make_tag(pos='u'):
            c = counter.get(pos, 0) + 1
            counter[pos] = c
            return '%s%d'%(pos, c)

        for i, c in enumerate(raw):
            if c == '[':
                istrans = True
                operator.append((']', i));
                pos = 't'
                buff = ""
            elif c == '{':
                operator.append(('}', i));
                pos = buff
                buff = ""
            elif c == '(':
                operator.append((')', i))
                pos = make_tag(buff)
                buff = ""
            elif c == ' ' and buff == "": pass
            elif c in ' ,)}' and ishashtag:
                ishashtag = False
                # if buff is not buff.strip(): raise Exception(raw, buff)
                if not operator: pos = ""
                hashtag[buff] = hashtag.get(buff, []) + [pos]
                buff = ""
            elif c == '#':
                ishashtag = True;
                if pos == "": pos = make_tag()
                if buff.strip():
                    output[pos] = output.get(pos, []) + [ buff.strip() ]
                buff = "#"
            elif c == ',':
                if pos == "": pos = make_tag()
                if buff.strip():
                    output[pos] = output.get(pos, []) + [ buff.strip() ]
                buff = ""
            elif c in '])}':
                try:
                    symbol, index = operator.pop()
                except Exception as e:
                    print(raw)
                    raise
                if c != symbol:
                    print('buffer: "%s"'%buff, 'got: "%s"'%c, 'expected: "%s"'%symbol)
                    raise Exception("error: unbalanced paranthesis")

                # if buff is not buff.strip(): raise Exception(raw, buff)
                if buff.strip():
                    output[pos] = output.get(pos, []) + [ buff.strip() ]
                buff = ""
                if c == ')': pos  = ""
            else:
                buff += c

        if buff != "":
            if ishashtag:
                hashtag[buff.strip()] = hashtag.get(buff.strip(), [""])
            else:
                if pos == "": pos = make_tag()
                output[pos] = output.get(pos, []) + [ buff.strip() ]

        output['#'] = hashtag
        return output


    @staticmethod
    def reload():
        for path, instance in __class__.instances.items():
            del instance
            Glossary(path)


    @staticmethod
    def search_hashtag(tag):
        query = tag[1:]
        FULL, FUZZ = OrderedDict(), dict()
        for path, instance in __class__.instances.items():
            for name, (liststore, invert) in instance.items():
                for word, (ID, info) in liststore.items():
                    if query == word:
                        FULL[(word, ID, path + name)] = info
                        continue
                    for tag, pos in info['#'].items():
                        # WISH: #animal.reptile.snake, #snake will match same
                        # this is only required for console
                        if query not in tag: continue
                        FUZZ[(word, ID, path + name)] = info

        return FULL, FUZZ


    @staticmethod
    def search(query):
        FULL, FUZZ = OrderedDict(), dict()
        def match(iterable):
            for word, (ID, info) in iterable.items():
                d = edit_distance(query, word)
                if d > 1 and query not in word: continue
                if d: FUZZ[(word, ID, src)] = info
                else: FULL[(word, ID, src)] = info

        for path, instance in __class__.instances.items():
            for name, (liststore, invert) in instance.items():
                src = path + name
                match(liststore)
                match(invert)

        return FULL, FUZZ


def load_from_config(cnf):
    count = 0
    for gloss in sorted(cnf.glossary_list, key=lambda v: v['priority']):
        # while loop for reloading
        n = 0
        path = gloss['path']
        while n < len(gloss['pairs']):
            try:
                g = Glossary(path + gloss['pairs'][n] + '/')
                gloss['error'] = True
            except NotADirectoryError as e:
                print(e)
                n += 1
                continue
            except Exception as e:
                traceback.print_exception(*sys.exc_info())
                # TODO robustness and show error in gui
                if not cnf.core['gloss-fix']:
                    n += 1
                    continue
                cmd = cnf.editor_goto_line_uri(*e.meta_info)
                # NOTE: we need something to hang on till we edit
                ## vvvv DON'T USES Popen vvvv
                if os.system(' '.join(cmd)): exit()
                print('RELOAD')
                continue
            n += 1
            count += 1
    return count


def sample():
    import setting
    cnf = setting.main()
    cnf.core['gloss-fix'] = False
    load_from_config(cnf)


if __name__ == '__main__':
    import doctest
    doctest.testmod()

    sample()
    from pprint import pprint
    pprint(Glossary.search('hello'))
    pprint(Glossary.search('lavender'))
    FULL, FUZZ = Glossary.search_hashtag('#color')
    pprint(FULL)
    print([ word for word, ID, src in FUZZ.keys() ])
