#!/usr/bin/env python3

import os, sys

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Pango
from nltk.corpus import wordnet as wn

import viewer as Vi

class Relatives(Gtk.Expander):
    types = (
        'Synonyms',
        'Antonyms',
        'Derivatives',
        'Relates to' ,#Pertainyms
        'Attributes',
        'Similar',
        'Domain',
        'Casuses',
        'Entails',
        'Kind of', #Hypernyms
        'Kinds', #Hyponyms
        'Part of', #Holonyms
        'Parts', #Meronyms
    )
    pages = {}
    def __init__(self, parent=None):
        Gtk.Expander.__init__(self)
        self.parent = parent
        self.makeWidgets()

        self.set_label("Relatives")
        self.set_expanded(True)
        self.show_all()

    def makeWidgets(self):
        self.notebook = Gtk.Notebook()
        self.add(self.notebook)
        self.notebook.set_tab_pos(Gtk.PositionType.LEFT)
        self.notebook.set_scrollable(True)
        self.notebook.set_show_border(True)
        self.notebook.set_border_width(10)
        #self.notebook.set_border(10)

        for text in Relatives.types:
            obj = Gtk.ScrolledWindow()
            obj.treemodel = Gtk.ListStore(int, str)
            obj.treeview = Gtk.TreeView(obj.treemodel)
            obj.add(obj.treeview)

            obj.treeview.set_headers_visible(False)
            renderer_text = Gtk.CellRendererText()
            obj.treeview.append_column(Gtk.TreeViewColumn("#", renderer_text, text=0))
            obj.treeview.append_column(Gtk.TreeViewColumn("w", renderer_text, text=1))

            self.notebook.append_page(obj, Gtk.Label(label=text))
            Relatives.pages[text] = obj


def search_wordnet(view, query):
    end = view.textbuffer.get_end_iter()
    view.textbuffer.insert_with_tags(end, query + '\n', view.tag_bold)

    synonyms = []
    count = 0
    for i, syn in enumerate(wn.synsets(query), 1):
        # print(syn.hypernyms(), syn.root_hypernyms())
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
    root.connect('key_release_event', Vi.root_binds)
    root.set_default_size(500, 600)

    root.layout = Gtk.VBox(root)
    root.add(root.layout)
    return root


if __name__ == '__main__':
    exec(open("mysettings.conf", encoding="UTF-8").read())
    FONT_obj =  Pango.font_description_from_string(def_FONT)
    root = main()

    obj = Vi.Viewer(root)
    root.layout.add(obj)

    obj.textview.modify_font(FONT_obj)
    # obj.parse([1, 'hello', 'नमस्कार'])

    relatives = Relatives(root.layout)
    root.layout.add(relatives)

    query = sys.argv[1] if len(sys.argv) > 1 else "hello"
    search_wordnet(obj, query)
    root.show_all()
    Gtk.main()
