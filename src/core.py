#!/usr/bin/env python3

import os, sys

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

fp3 = sys.stderr
fp4 = sys.stderr
FILE_TYPES = ["tsl", "fun", "abb", "tra", "txt"]
pos_map = {
    'n': "noun",
    'noun': "noun",
    'j': "adjective",
    'adj': "adjective",
    'v': "verb",
}

class Glossary():
    instances = []
    total_entries = 0

    def __init__(self, path):
        self.entries = 0
        self.categories = dict()
        self.fullpath = PATH_GLOSS + path

        self.load_glossary(self.fullpath)
        print("glossary:", path, self.entries, file=sys.stderr)

        __class__.instances.append(self)
        __class__.total_entries += self.entries


    def load_glossary(self, path):
        if not os.path.isdir(path):
            print("error: invalid glossary path ", file=sys.stderr)
            return

        for file in os.listdir(path):
            name, dot, ext = file.rpartition('.')
            if ext not in FILE_TYPES: continue
            category = self.load_entries(self.fullpath + file)
            self.categories[name] = category


    def load_entries(self, path):
        print("loading: *" + path[-40:], file=fp4)
        liststore = Gtk.ListStore(int, str, str)
        invert = dict()

        try:
            data = open(path, encoding="UTF-8").read()
        except:
            print("error: in file", path)
            return

        for i, line in enumerate(data.splitlines(), 1):
            try:
                word, defination = line.split('; ')
            except Exception as e:
                print("fatal:", e)
                print("wrong format %s: %d"%(src, i))
                # NOTE: we need something to hang on till we edit
                ## print("pid:", Popen(["leafpad", arg, self.SRC]).pid)
                ## DONT USES Popen ^^^^
                os.system("setsid leafpad --jump=%d %s"%(i, src))
                exit(1)
            liststore.append((i, word, defination))
            parsed_info = self.format_parser(defination)
            for pos, val in parsed_info:
                try:
                    if   pos[0] == "_" or val == "": continue
                except:
                    print(i, pos, val)
                    exit()

                if pos == "transliterate": continue
                # TODO make list of words connected
                invert[val] = word

        self.entries += i
        return (liststore, invert, path)


    # def reload(self, gloss):
    #     GLOSS = PATH_GLOSS + gloss
    #     if self.notebook.GLOSS == GLOSS: return

    #     self.layout.remove(self.notebook)
    #     for obj in GUI.notebook_OBJS:
    #         if obj.GLOSS == GLOSS:
    #             self.notebook = obj
    #             break
    #     else:
    #         self.notebook = self.makeWidgets_browser(gloss)

    #     self.layout.attach(self.notebook, 0, 5, 5, 2)
    #     self.show_all()
    #     self.notebook.set_current_page(self.notebook.MAIN_TAB)


    # def _reload_gloss(self):
    #     current_tab = self.notebook.get_current_page()
    #     obj = self.notebook.get_nth_page(current_tab)
    #     obj.reload()


    @staticmethod
    def format_parser(raw):
        """
        >>> print("Test 07"); Glossary.format_parser('[मस्टर्ड] n(<leaves>रायोको साग), #vegetable')
        Test 07
        [('_transliterate', 'मस्टर्ड'), ('_note', 'leaves'), ('noun', 'रायोको साग'), ('unknown', ''), ('unknown', ''), ('_#', 'vegetable')]
        >>> print("Test 06"); Glossary.format_parser('[वीट्] n(गहूँ) #crop, wiki{Wheat}')
        Test 06
        [('_transliterate', 'वीट्'), ('noun', 'गहूँ'), ('unknown', ''), ('_#', 'crop'), ('_wiki', 'Wheat')]
        >>> print("Test 05"); Glossary.format_parser('[शेल] n(शंख किरो #animal), n(छिल्का, खोल, बोक्रा)')
        Test 05
        [('_transliterate', 'शेल'), ('noun', 'शंख किरो'), ('_#', 'animal'), ('noun', ''), ('noun', 'छिल्का'), ('noun', 'खोल'), ('noun', 'बोक्रा')]
        >>> print("Test 04"); Glossary.format_parser('[हेल्‍लो] n(नमस्कार, नमस्ते), v(स्वागत, अभिवादन, सम्बोधन, जदौ)')
        Test 04
        [('_transliterate', 'हेल्\u200dलो'), ('noun', 'नमस्कार'), ('noun', 'नमस्ते'), ('unknown', ''), ('verb', 'स्वागत'), ('verb', 'अभिवादन'), ('verb', 'सम्बोधन'), ('verb', 'जदौ')]
        >>> print("Test 03"); Glossary.format_parser('n(<thin> तुवाँलो ~fog)')
        Test 03
        [('_note', 'thin'), ('noun', 'तुवाँलो ~fog')]
        >>> print("Test 02"); Glossary.format_parser('कर')
        Test 02
        [('unknown', 'कर')]
        >>> print("Test 01"); Glossary.format_parser('n:v(मस्त)')
        Test 01
        [('noun:verb', 'मस्त')]
        """

        operator, output = [], []
        pos = 'unknown'
        buffer = ""
        fbreak = 0
        hashtag = False
        note = False
        # TODO: refacator, reduce repeted segements
        for i, c in enumerate(raw.strip()): # bored strip!
            if   c == '[':
                operator.append((']', i));
                pos = '_transliterate'
                fbreak = i + 1
                buffer = ""
            elif c == '<' and buffer == "":
                note = True
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
                note = False
            elif c == '#':
                hashtag = True;
                output.append((pos, buffer.strip()))
                buffer = ""
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

        return output


    @staticmethod
    def search(query):
        FULL, FUZZ = [], []
        for instance in __class__.instances:
            for liststore, invert, path in instance.categories.values():
                for row in liststore:
                    if query not in row[1]: continue
                    match = (instance, path, tuple(row))
                    if query == row[1]: FULL.append(match)
                    else: FUZZ.append(match)

                if query in invert.keys():
                    # TODO get location
                    match = (instance, path, (1, query, invert[query]))
                    FULL.append(match)

        return FULL, FUZZ


if __name__ == '__main__':
    exec(open("gsettings.conf", encoding="UTF-8").read())
    foss_gloss = Glossary(LIST_GLOSS[0])
    FULL, FUZZ = Glossary.search('hello')
    if FULL:
        print(FULL[0][2][:])
    import doctest
    doctest.testmod()
