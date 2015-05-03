#!/usr/bin/env python

import os, sys

exec(open("mysettings.conf").read())
if PATH_MYLIB and os.path.isdir(PATH_MYLIB):
    sys.path.append(PATH_MYLIB)
    from debugly import *

from subprocess import Popen
from gi.repository import Gtk, Gdk, Pango

class BrowseList(Gtk.ScrolledWindow):
    """
    >>> obj = BrowseList(parent=root)
    >>> root.add(obj)
    """
    def __init__(self, parent=None, src=None):
        Gtk.ScrolledWindow.__init__(self)
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.SRC = src
        self.liststore = Gtk.ListStore(int, str, str)
        self.makeWidgets()

        if self.SRC:
            print("loading: *" + src[-40:])
            self.fill_tree(src)


    def makeWidgets(self):
        self.treeview = Gtk.TreeView(model=self.liststore)
        self.add(self.treeview)
        self.treeview.connect('key_press_event', self.treeview_key_press)

        renderer_text = Gtk.CellRendererText()
        c0 = Gtk.TreeViewColumn("#", renderer_text, text=0)
        self.treeview.append_column(c0)

        c1 = Gtk.TreeViewColumn("English", renderer_text, text=1)
        self.treeview.append_column(c1)

        renderer_editabletext = Gtk.CellRendererText()
        renderer_editabletext.set_property("editable", False)

        c2 = Gtk.TreeViewColumn("नेपाली", renderer_editabletext, text=2)
        self.treeview.append_column(c2)

        renderer_editabletext.connect("edited", self.text_edited)


    def treeview_key_press(self, widget, event):
        if Gdk.ModifierType.CONTROL_MASK & event.state:
            if event.keyval == ord('u'):
                self.open_src()


    def text_edited(self, widget, path, text):
        self.liststore[path][2] = text


    def fill_tree(self, _gloss):
        data = open(_gloss, encoding="UTF-8").read()
        self.count = 0

        for line in data.splitlines():
            self.count += 1
            row = line.split('; ')
            if len(row) != 2:
                # TODO: open leafpad automatically with the current error line
                print("File Format Error: %s: %d"%(self.SRC, self.count))
                arg = "--jump=%d"%self.count
                os.system("setsid leafpad %s %s"%(arg, self.SRC))
                exit(1)
            row.insert(0, self.count)
            self.liststore.append(row)


    def add_to_tree(self, row):
        self.count += 1
        self.liststore.append([self.count] + row)
        return self.count


    def clear_tree(self):
        pass


    def reload_tree(self):
        pass


    def open_src(self, ID=None):
        # TODO : smart xdg-open with arguments
        # if not self.CURRENT_FOUND_ITEM:
        #     open_src()
        #     return
        if ID:
            arg = "--jump=%d"%ID
            print(Popen(["leafpad", arg, self.SRC]).pid)
        else:
            print(Popen(["leafpad", self.SRC]).pid)


    def make_popup(self, ID, word):
        # popup = Menu(self, tearoff=0)
        # popup.add_command(label=ID + ' : ' + word, state=DISABLED, font=self.h1)
        # popup.add_command(label="Edit", command=lambda: open_src())
        # popup.add_command(label="Open Gloss", command=lambda: open_src())
        # popup.add_separator()
        # popup.add_command(label="Search online", command=lambda: web_search(word))
        # return popup
        pass

    def get_ID_below_mouse(self, event):
        # ID = ttk.Treeview.identify(self.tree, component='item', x=ex, y=ey)

        # self.tree.selection_set(ID)
        # self.tree.focus(ID)
        # self.tree.focus_set()

        # return ID
        pass


    def call_popup(self, event):
        # ID = self.get_ID_below_mouse(event)
        # word = self.tree.item(ID)['values'][1]
        # popup = self.make_popup(ID, word)
        # popup.tk_popup(event.x_root, event.y_root)
        # del popup
        pass


def on_key_press(widget, event):
    # print(event.keyval)
    if event.keyval == 65307:
        Gtk.main_quit()


def main():
    global def_font
    def_font = ["DejaVuSansMono", 12, "normal"]

    global root
    root = Gtk.Window()
    root.connect('delete-event', Gtk.main_quit)
    root.connect('key_release_event', on_key_press)
    root.set_default_size(600, 300)


if __name__ == '__main__':
    main()
    import doctest
    doctest.testmod()
    root.show_all()
    Gtk.main()
