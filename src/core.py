#!/usr/bin/env python3

import os, sys
import distance

fp3 = fp4 = sys.stderr
FILE_TYPES = ["tsl", "fun", "abb", "tra", "txt"]
pos_map = {
    'n'    : "noun",
    'j'    : "adjective",
    'adj'  : "adjective",
    'v'    : "verb",
    'm'    : "meaning",
}

class Glossary:
    instances = []
    hashtag = set() # for auto-complete

    def __init__(self, path):
        self.entries = 0
        self.categories = dict()
        self.fullpath = os.path.expanduser(path)
        self.load_glossary(self.fullpath)
        print("glossary:", path, self.entries, file=sys.stderr)

        __class__.instances.append(self)


    def load_glossary(self, path):
        if not os.path.isdir(path):
            print("error: invalid glossary path ", file=sys.stderr)
            return

        for _file in os.listdir(path):
            name, dot, ext = _file.rpartition('.')
            if ext not in FILE_TYPES: continue
            category = self.load_entries(self.fullpath + _file)
            self.categories[name] = category


    def load_entries(self, path):
        print("loading: *" + path[-40:], file=fp4)
        liststore = dict()
        invert = dict()

        try:
            data = open(path, encoding="UTF-8").read()
        except:
            print("error: in file", path, file=sys.stderr)
            return

        for i, line in enumerate(data.splitlines(), 1):
            try:
                word, defination = line.split('; ')
            except Exception as e:
                print("fatal:", e, file=sys.stderr)
                print("wrong format %s: %d"%(path, i), file=sys.stderr)
                e.meta_info = (path, i)
                raise

            parsed_info = self.format_parser(defination)

            has_hashtag = False
            for pos, val in parsed_info:
                if pos == '_#':
                    __class__.hashtag.add(val)
                    has_hashtag = True
                    continue

                if   pos[0] == '_': continue
                elif val    == '': continue

                # inverted list
                ID, info = invert.get(val, (tuple(), tuple()))
                invert[val] = (
                    ID + tuple([i]),
                    info + (tuple([pos, word]), ),
                )

            duplicate = liststore.get(word)
            if duplicate:
                print("repeated entry:", word, file=sys.stderr)
                print("%s: %d == %d"%(path, i, duplicate[0]), file=sys.stderr)
                e = Exception('Repeated entries')
                e.meta_info = (path, i)
                raise e

            liststore[word] = (i, has_hashtag, parsed_info)

        self.entries += i
        return (liststore, invert, path)


    @staticmethod
    def format_parser(raw):
        """
        >>> print("Test 08"); Glossary.format_parser('सृजना <कीर्ति>')
        Test 08
        (('unknown', 'सृजना'), ('_note', 'कीर्ति'))
        >>> print("Test 07"); Glossary.format_parser('[मस्टर्ड] n(<leaves>रायोको साग), #vegetable')
        Test 07
        (('_transliterate', 'मस्टर्ड'), ('noun', ''), ('_note', 'leaves'), ('noun', 'रायोको साग'), ('unknown', ''), ('unknown', ''), ('_#', '#vegetable'))
        >>> print("Test 06"); Glossary.format_parser('[वीट्] n(गहूँ) #crop, wiki{Wheat}')
        Test 06
        (('_transliterate', 'वीट्'), ('noun', 'गहूँ'), ('unknown', ''), ('_#', '#crop'), ('_wiki', 'Wheat'))
        >>> print("Test 05"); Glossary.format_parser('[शेल] n(शंख किरो #animal), n(छिल्का, खोल, बोक्रा)')
        Test 05
        (('_transliterate', 'शेल'), ('noun', 'शंख किरो'), ('_#', '#animal'), ('noun', ''), ('noun', 'छिल्का'), ('noun', 'खोल'), ('noun', 'बोक्रा'))
        >>> print("Test 04"); Glossary.format_parser('[हेल्‍लो] n(नमस्कार, नमस्ते), v(स्वागत, अभिवादन, सम्बोधन, जदौ)')
        Test 04
        (('_transliterate', 'हेल्\u200dलो'), ('noun', 'नमस्कार'), ('noun', 'नमस्ते'), ('unknown', ''), ('verb', 'स्वागत'), ('verb', 'अभिवादन'), ('verb', 'सम्बोधन'), ('verb', 'जदौ'))
        >>> print("Test 03"); Glossary.format_parser('n(<thin> तुवाँलो ~fog)')
        Test 03
        (('noun', ''), ('_note', 'thin'), ('noun', 'तुवाँलो ~fog'))
        >>> print("Test 02"); Glossary.format_parser('कर')
        Test 02
        (('unknown', 'कर'),)
        >>> print("Test 01"); Glossary.format_parser('n:v(मस्त)')
        Test 01
        (('noun:verb', 'मस्त'),)
        """

        operator, output = [], []
        pos = 'unknown'
        buffer = ""
        fbreak = 0
        hashtag = False
        note = False
        # TODO: refacator, reduce repeted segements
        # TODO: don't separte segment by unknown
        for i, c in enumerate(raw.strip()): # bored strip!
            if   c == '[':
                operator.append((']', i));
                pos = '_transliterate'
                fbreak = i + 1
                buffer = ""
            elif c == '<':
                note = True
                output.append((pos, buffer.strip()))
                buffer = ""
            elif c == '{':
                operator.append(('}', i));
                pos = '_' + buffer # '_' prefix for meta tags
                fbreak = i + 1
                buffer = ""
            elif c == '(':
                operator.append((')', i))
                pos = ':'.join(pos_map.get(b, b) for b in buffer.split(':'))
                fbreak = i + 1
                buffer = ""
            elif c == ' ' and buffer == "": pass
            elif c in ' ,)>}' and hashtag:
                output.append(("_#", buffer.strip()))
                buffer = ""
                hashtag = False
            elif c in '>':
                output.append(("_note", buffer.strip()))
                buffer = ""
            elif c == '#':
                hashtag = True;
                output.append((pos, buffer.strip()))
                buffer = "#"
            elif c == ',':
                # print(buffer, file=fp3)
                output.append((pos, buffer.strip()))
                buffer = ""
                fbreak = i + 1
            elif c in '])}':
                try:
                    symbol, index = operator.pop()
                except Exception as e:
                    print(e)
                    print(raw)
                    exit()
                if c != symbol:
                    print('buffer: "%s"'%buffer, 'got: "%s"'%c, 'expected: "%s"'%symbol)
                    print("error: unbalanced paranthesis", file=sys.stderr)
                    return # TODO error handling
                output.append((pos, buffer.strip()))
                buffer = ""
                fbreak = i + 1
                pos = 'unknown'
            else:
                buffer += c

        if buffer != "":
            if hashtag: pos = '_#'
            output.append((pos, buffer.strip()))

        return tuple(output)


    @staticmethod
    def search_hashtag(query):
        FULL, FUZZ = [], []
        for instance in __class__.instances:
            for liststore, invert, path in instance.categories.values():
                for word, (ID, *has_hashtag, info) in liststore.items():
                    if len(has_hashtag) == 0: continue
                    if has_hashtag[0] is False: continue
                    for pos, val in info:
                        if "_#" != pos: continue
                        if query not in val: continue
                        match = (instance, path, (ID, word, info))
                        FUZZ.append(match)

        return FULL, FUZZ


    @staticmethod
    def search(query):
        FULL, FUZZ = [], []
        def traverse_dict(iterable):
            for word, (ID, *has_hashtag, info) in iterable.items():
                d = distance.edit(query, word)
                if d > 1 and query not in word: continue
                match = (instance, path, (ID, word, info))
                if d: FUZZ.append(match)
                else: FULL.append(match)

        for instance in __class__.instances:
            for liststore, invert, path in instance.categories.values():
                traverse_dict(liststore)
                traverse_dict(invert)

        return FULL, FUZZ


def load_from_config(rc):
    for gloss in sorted(rc.glossary_list, key=lambda k: k['priority']):
        n = 0
        while n < len(gloss['pairs']):
            try:
                Glossary(gloss['pairs'][n])
            except Exception as e:
                cmd = rc.editor_goto_line_uri(*e.meta_info)
                os.system(' '.join(cmd))
                # NOTE: we need something to hang on till we edit
                ## DONT USES Popen ^^^^
                print('RELOAD')
                continue
            n += 1


if __name__ == '__main__':
    import config
    rc = config.main()

    load_from_config(rc)

    from pprint import pprint
    pprint(Glossary.search('hello'))
    pprint(Glossary.search_hashtag('#color'))

    import doctest
    doctest.testmod()
