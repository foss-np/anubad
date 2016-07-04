#!/usr/bin/env python3

import os, sys

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Pango

class Relatives(Gtk.Box):
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

    def __init__(self):
        Gtk.Box.__init__(self, name="Relatives")
        self.makeWidgets()


    def makeWidgets(self):
        self.notebook = Gtk.Notebook()
        self.add(self.notebook)

        self.notebook.set_hexpand(True)
        self.notebook.set_vexpand(True)

        self.notebook.set_tab_pos(Gtk.PositionType.LEFT)
        self.notebook.set_scrollable(True)
        self.notebook.set_show_border(False)

        for text in Relatives.types:
            obj = Gtk.ScrolledWindow()
            obj.treemodel = Gtk.ListStore(int, str)
            obj.treeview = Gtk.TreeView(obj.treemodel)
            obj.add(obj.treeview)

            obj.treeview.set_enable_search(False)
            obj.treeview.set_headers_visible(False)

            renderer_text = Gtk.CellRendererText()
            obj.treeview.append_column(Gtk.TreeViewColumn("#", renderer_text, text=0))
            obj.treeview.append_column(Gtk.TreeViewColumn("w", renderer_text, text=1))

            self.notebook.append_page(obj, Gtk.Label(label=text))
            Relatives.pages[text.strip()] = obj


def sample():
    root = Gtk.Window()
    root.connect('delete-event', Gtk.main_quit)
    root.connect( # quit when Esc is pressed
        'key_release_event',
        lambda w, e: Gtk.main_quit() if e.keyval == 65307 else None
    )
    root.set_default_size(500, 300)

    root.layout = Gtk.VBox(root)
    root.add(root.layout)

    relatives = Relatives(root.layout)
    root.layout.add(relatives)

    root.show_all()
    return root


if __name__ == '__main__':
    sample()
    Gtk.main()
