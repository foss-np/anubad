#!/usr/bin/env python3

"""
WordNet Interface for Anubad
"""

import os, sys

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Pango
from nltk.corpus import wordnet as wn

def search_wordnet(view, relatives, query):
    end = view.textbuffer.get_end_iter()
    view.textbuffer.insert_with_tags(end, query + '\n', view.tag_bold)
    synonyms = []
    count = 0
    for i, syn in enumerate(wn.synsets(query), 1):
        #print(syn.hypernyms(), syn.root_hypernyms())
        for lemmas in syn.lemmas():
            name = lemmas.name().replace('_', ' ')
            if name not in synonyms:
                synonyms.append(name)
                count += 1
                relatives.pages['Synonyms'].treemodel.append((count, name))

        end = view.textbuffer.get_end_iter()
        view.textbuffer.insert_with_tags(end, "%4d. "%i, view.tag_li)
        end = view.textbuffer.get_end_iter()
        view.textbuffer.insert_with_tags(end, "%s » "%syn.pos(), view.tag_pos)
        end = view.textbuffer.get_end_iter()
        view.textbuffer.insert(end, "%s ~ %s\n"%(syn.name(), syn.definition()))
        for eg in syn.examples():
            end = view.textbuffer.get_end_iter()
            view.textbuffer.insert_with_tags(end, "%9s%s\n"%(' ',eg), view.tag_example)


def main():
    global clipboard
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

    global root
    root = Gtk.Window()
    root.connect('delete-event', Gtk.main_quit)
    root.connect('key_release_event', viewer.root_binds)
    root.set_default_size(500, 600)

    root.layout = Gtk.VBox(root)
    root.add(root.layout)
    return root


if __name__ == '__main__':
    exec(open("mysettings.conf", encoding="UTF-8").read())
    FONT_obj =  Pango.font_description_from_string(def_FONT)

    import viewer
    import relation

    root = main()

    obj = viewer.Display(root)
    root.layout.add(obj)

    obj.textview.modify_font(FONT_obj)
    # obj.parse([1, 'hello', 'नमस्कार'])

    relatives = relation.Relatives(root.layout)
    root.layout.add(relation)

    query = sys.argv[1] if len(sys.argv) > 1 else "hello"
    search_wordnet(obj, relation, query)
    root.show_all()
    Gtk.main()
