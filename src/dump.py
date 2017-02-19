#!/usr/bin/env python3

"""way to do json dump"""

import json

import core
import setting

cnf = setting.main()
core.load_from_config(cnf)

with open("gloss.dump.json", 'w') as fp:
    for instance in core.Glossary.instances.values():

        liststore, invert = instance['food.tra']
        clean = []

        for word, (ID, info) in liststore.items():
            # p POS_MAP.get(p[:-1]):
            
            empty_info = dict()
            empty_info['w'] = word
            for tag, value in info.items():
                # print("tag=",tag," value=", value)

                # extracting the scientific name
                if tag == "sci":
                  empty_info['sci'] = value

                if not tag[-1].isdigit(): continue
                pos = empty_info.get(tag[:-1], [])
                pos_obj = {
                    "tr": value
                }
                for hashtag, p in info['#'].items():
                    if tag not in p: continue
                    pos_obj["#"] = hashtag

                # tag= t  value= {'विन्ड': ['n1'], 'वाइड': ['v1']}
                for t, p in info['t'].items():
                    if tag not in p: continue 
                    pos_obj["t"] = t

                pos.append(pos_obj)
                # print(pos)
                empty_info[tag[:-1]] = pos
                
            # handling the global tags
            for hashtag, p in info['#'].items():
                # print(hashtag, p)
                if "" not in p: continue
                gtag = empty_info.get("#",[])
                gtag.append(hashtag)
                empty_info["#"] = gtag
            print(empty_info)
            # exit()

            # get more hash
            clean.append(empty_info)
        json.dump(clean, fp, ensure_ascii=False)
        break
