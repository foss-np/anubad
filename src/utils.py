#!/usr/bin/env python3

import os
import tarfile
from urllib.request import urlopen

import setting

def get_gloss(gloss):
    url = gloss['fetch']
    name  = os.path.basename(url)

    path_cache = os.path.expanduser(setting.PATH_CACHE) + 'gloss/'
    os.makedirs(path_cache, exist_ok=True)
    file_gloss = path_cache + name
    if not os.path.isfile(file_gloss):
        raw = urlopen(url).read()
        fp = open(file_gloss, 'wb')
        fp.write(raw)
        fp.close()

    tar = tarfile.open(file_gloss, "r:gz")
    tar.extractall(path_cache)
    tar.close()


def check_gloss(gloss):
    path = os.path.expanduser(gloss['path'])
    if os.path.isdir(path):
        print(gloss['name'], 'already exists')
        return

    get_gloss(gloss)

if __name__ == '__main__':
    cnf = setting.Settings()
    cnf.read(setting.FILE_DEFAULT_INI)
    cnf.load()

    for gloss in cnf.glossary_list:
        check_gloss(gloss)
