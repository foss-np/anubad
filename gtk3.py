#!/usr/bin/env python

import os, sys

filepath = os.path.abspath(__file__)
fullpath = os.path.dirname(filepath) + '/'

exec(open(fullpath+"gsettings.conf").read())
exec(open(fullpath+"mysettings.conf").read())

PATH_GLOSS = fullpath + PATH_GLOSS

if PATH_MYLIB:
    sys.path.append(PATH_MYLIB)
    from debugly import *

from gi.repository import Gtk, Gdk, Pango
import browselst2 as BL
import viewer2 as Vi

class GUI(Gtk.Grid):
    def __init__(self, parent=None):
        Gtk.Grid.__init__(self)
        self.parent = parent
        self.makeWidgets()


    def makeWidgets(self ):
        ## Combo box
        label = Gtk.Label("Query")
        self.attach(label, 0, 0, 1, 1)

        self.search_history = Gtk.ListStore(int, str)
        self.cb_search = Gtk.ComboBox.new_with_model_and_entry(self.search_history)
        self.cb_search.set_entry_text_column(1)
        self.attach(self.cb_search, 1, 0, 1, 1)

        ### binding
        self.cb_search.connect('key_release_event', self.cb_binds)
        accel_search = Gtk.AccelGroup()
        root.add_accel_group(accel_search)
        self.cb_search.add_accelerator("grab_focus", accel_search, ord('f'), Gdk.ModifierType.CONTROL_MASK, 0)
        self.cb_search.add_accelerator("grab_focus", accel_search, ord('s'), Gdk.ModifierType.CONTROL_MASK, 0)
        self.cb_search.add_accelerator("grab_focus", accel_search, ord('l'), Gdk.ModifierType.CONTROL_MASK, 0)

        ## Button
        self.b_search = Gtk.Button(label="Search")
        self.b_search.connect('clicked', lambda e: self.searchWord())
        self.attach(self.b_search, 2, 0, 1, 1)

        ## Viewer
        self.textview = Vi.Viewer(self)
        self.attach(self.textview, 0, 1, 3, 2)

        ## browser
        self.lview = BL.BrowseList(self.parent, PATH_GLOSS+'main.tra')
        self.attach(self.lview, 0, 3, 3, 1)


    def cb_binds(self, widget, event):
        # print(event.keyval, event.type)
        if event.keyval == 65293: # return key
            self.searchWord()
            self.cb_search.grab_focus()


    def searchWord(self):
        entry = self.cb_search.get_child()
        val = entry.get_text().strip().lower()

        foundFlag = False
        tab = 0
        for i in self.lview.liststore:
            if i[1] != val : continue
            self.textview.parser([tab] + list(i))
            foundFlag = True
            break

        if foundFlag is False:
            self.textview.not_found(val)


def on_key_press(widget, event):
    # print(event.keyval)
    if event.keyval == 65307:
        Gtk.main_quit()

    if Gdk.ModifierType.CONTROL_MASK & event.state:
        if event.keyval == ord('c'):
            entry = gui.cb_search.get_child()
            entry.set_text("")


def main():
    global root
    root = Gtk.Window()
    root.connect('delete-event', Gtk.main_quit)
    root.connect('key_release_event', on_key_press)
    root.set_default_size(600, 500)

    global gui
    gui = GUI(root)

    root.add(gui)


if __name__ == '__main__':
    main()
    root.show_all()
    Gtk.main()
