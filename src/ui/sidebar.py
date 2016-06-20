#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class Bar(Gtk.VBox):
    def __init__(self, parent=None):
        Gtk.HBox.__init__(self)
        self.parent = parent
        self.track_FONT = set()
        self.count = 0
        self.dictstore = dict()
        self.makeWidgets()


    def makeWidgets(self):
        self.pack_start(self.makeWidgets_treeview(), True, True, 0)
        self.track_FONT.add(self.treeview)
        treeselection = self.treeview.get_selection()
        treeselection.set_mode(Gtk.SelectionMode.MULTIPLE)

        self.cb_filter = Gtk.ComboBoxText()
        self.pack_start(self.cb_filter, False, False, 0)
        self.cb_filter.append_text("All")
        self.cb_filter.set_active(0)


    def add_suggestion(self, key, value):
        # if key in self.dictstore.values(): return
        self.count += 1
        self.treemodel.append((self.count, key[0]))
        word, ID, src = key
        # NOTE: unpacking variable, seems some python version
        # only supports named args followed by *expression
        # ref: https://github.com/foss-np/anubad/issues/11
        self.dictstore[self.count] = (word, ID, src, value)


    def get_suggestion(self, index):
        c, word = self.treemodel[index]
        return self.dictstore[c]


    def clear(self):
        self.treemodel.clear()
        self.dictstore.clear()
        self.count = 0


    def makeWidgets_treeview(self):
        scroll = Gtk.ScrolledWindow()
        scroll.set_hexpand(True)
        scroll.set_vexpand(True)

        self.treemodel = Gtk.ListStore(int, str)

        self.treeview = Gtk.TreeView(self.treemodel)
        scroll.add(self.treeview)

        self.treeview.set_enable_search(False)
        self.treeview.set_headers_visible(False)
        self.treeview.set_rubber_banding(True)

        renderer_text = Gtk.CellRendererText()
        self.treeview.append_column(Gtk.TreeViewColumn("#", renderer_text, text=0))
        self.treeview.append_column(Gtk.TreeViewColumn("w", renderer_text, text=1))
        return scroll


def sample():
    root = Gtk.Window()
    root.connect('delete-event', Gtk.main_quit)
    root.connect( # quit when Esc is pressed
        'key_release_event',
        lambda w, e: Gtk.main_quit() if e.keyval == 65307 else None
    )
    root.set_default_size(300, 200)

    sidebar = Bar(root)
    root.add(sidebar)
    root.show_all()
    return root


if __name__ == '__main__':
    sample()
    Gtk.main()
