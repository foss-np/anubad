#!/usr/bin/env python3

import os, sys
from gi.repository import Gtk

fp_dev_null = open(os.devnull, 'w')
FILE_TYPES = ["tsl", "fun", "abb", "tra", "txt"]

class Glossary():
    instances = []
    def __init__(self, path):
        print("glossary:", path, file=sys.stderr)
        self.fullpath = PATH_GLOSS + path
        self.categories = dict()
        self.load_glossary(self.fullpath)
        __class__.instances.append(self)


    def load_glossary(self, path):
        if not os.path.isdir(path):
            print("error: invalid glossary path ", file=sys.stderr)
            return

        for file in os.listdir(path):
            name, dot, ext = file.rpartition('.')
            if ext not in FILE_TYPES: continue
            lstore = Gtk.ListStore(int, str, str)
            lstore.fullpath = path + file
            self.load_entries(lstore, self.fullpath + file)
            self.categories[name] = lstore


    def load_entries(self, category, src):
        print("loading: *" + src[-40:], file=fp_dev_null)

        try:
            data = open(src, encoding="UTF-8").read()
        except:
            print("error: in file", src)
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
            category.append((i, word, defination))


    @staticmethod
    def search(query):
        FULL, FUZZ = [], set()
        for instance in __class__.instances:
            for category in instance.categories.values():
                for row in category:
                    if query not in row[1]: continue
                    match = (instance, category, row)
                    if query == row[1]: FULL.append(match)
                    else: FUZZ.add(match)
        return FULL, FUZZ


if __name__ == '__main__':
    exec(open("gsettings.conf").read())
    foss_gloss = Glossary(LIST_GLOSS[0])
    FULL, FUZZ = gloss.search('hello')

    print(FULL[0][2][:])
