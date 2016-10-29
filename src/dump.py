#!/usr/bin/env python3

"""way to do json dump"""

import json

import core
import setting

cnf = setting.main()
core.load_from_config(cnf)

with open("gloss.dump", 'w') as fp:
    for instance in core.Glossary.instances.values():
        # dump = { name: liststore for name, (liststore, invert) in instance.items() }
        # json.dump(dump, fp, ensure_ascii=False)
        json.dump(instance['main.tra'][0], fp, ensure_ascii=False)
        break
