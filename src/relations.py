#!/usr/bin/env python3

import os, sys

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Pango

class Relatives(Gtk.Expander):
    types = (
        '    Synonyms    ', #SPACE HACK for width
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

        self.notebook.set_hexpand(True)
        self.notebook.set_vexpand(True)

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


def root_binds(widget, event):
    # print(event.keyval)
    if event.keyval == 65307:
        Gtk.main_quit()


def main():
    global clipboard
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

    global root
    root = Gtk.Window()
    root.connect('delete-event', Gtk.main_quit)
    root.connect('key_release_event', root_binds)
    root.set_default_size(500, 300)

    root.layout = Gtk.VBox(root)
    root.add(root.layout)
    return root


if __name__ == '__main__':
    root = main()

    relatives = Relatives(root.layout)
    root.layout.add(relatives)

    root.show_all()
    Gtk.main()
