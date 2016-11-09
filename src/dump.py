#!/usr/bin/env python3

"""way to do json dump"""

import json

import core
import setting

cnf = setting.main()
core.load_from_config(cnf)

with open("gloss.dump", 'w') as fp:
    for instance in core.Glossary.instances.values():
        liststore, invert = instance['main.tra']
        clean = dict()
        for word, (ID, *has_hashtag, info) in liststore.items():
            # p POS_MAP.get(p[:-1]):
            clean[word] = info
        json.dump(clean, fp, ensure_ascii=False)
        break
