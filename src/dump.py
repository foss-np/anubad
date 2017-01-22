#!/usr/bin/env python3

"""way to do json dump"""

import json

import core
import setting

cnf = setting.main()
core.load_from_config(cnf)

with open("gloss.dump.json", 'w') as fp:
    for instance in core.Glossary.instances.values():

        liststore, invert = instance['main.tra']
        clean = []

        for word, (ID, info) in liststore.items():
            # p POS_MAP.get(p[:-1]):
            
            empty_info = dict()
            empty_info['w'] = word
            for tag, value in info.items():
                if not tag[-1].isdigit(): continue
                pos = empty_info.get(tag[:-1], [])
                pos_obj = {
                    "tr": value
                }
                for hashtag, p in info['#'].items():
                    if tag != p: continue
                    pos.get("#",[]).append(hashtag)

                pos.append(pos_obj)
                empty_info[tag[:-1]] = pos
                
                # print(tag, value)

            
            for hashtag, p in info['#'].items():
                # print(hashtag, p)
                if "" not in p: continue
                gtag = empty_info.get("#",[])
                gtag.append(hashtag)
                empty_info["#"] = gtag
                    
            # print(info)
            print(empty_info)
            # exit()

            # get more hash
            clean.append(empty_info)
        json.dump(clean, fp, ensure_ascii=False)
        break
