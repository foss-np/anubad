#!/usr/bin/env python3

import os, sys
from subprocess import Popen
from gi.repository import Gtk, Gdk, Pango

class BrowseList(Gtk.Overlay):
    def __init__(self, parent=None, lstore=None):
        Gtk.Overlay.__init__(self)
        if lstore is None:
            print("lstore canno't be None")
            exit()
        self.treebuffer = lstore
        self.makeWidgets(lstore)


    def makeWidgets(self, lstore):
        self.scroll = Gtk.ScrolledWindow()
        self.add(self.scroll)
        self.scroll.set_hexpand(True)
        self.scroll.set_vexpand(True)

        self.tool_b_Refresh = Gtk.ToolButton(icon_name=Gtk.STOCK_REFRESH)
        self.add_overlay(self.tool_b_Refresh)
        self.tool_b_Refresh.connect("clicked", lambda *a: self.reload())
        self.tool_b_Refresh.set_valign(Gtk.Align.START)
        self.tool_b_Refresh.set_halign(Gtk.Align.END)

        self.treeview = Gtk.TreeView(model=self.treebuffer)
        self.scroll.add(self.treeview)
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
        self.treebuffer[path][2] = text


    def reload(self):
        pass

    def open_src(self, ID=None):
        # TODO : smart xdg-open with arguments
        # if not self.CURRENT_FOUND_ITEM:
        #     open_src()
        #     return
        if ID:
            arg = "--jump=%d"%ID
            print("pid:", Popen(["leafpad", arg, self.SRC]).pid)
        else:
            print("pid:", Popen(["leafpad", self.treebuffer.fullpath]).pid)


def root_binds(widget, event):
    # print(event.keyval)
    if event.keyval == 65307:
        Gtk.main_quit()


def main():
    root = Gtk.Window()
    root.connect('delete-event', Gtk.main_quit)
    root.connect('key_release_event', root_binds)
    root.set_default_size(600, 300)

    return root


if __name__ == '__main__':
    fp3 = sys.stdout
    root = main()

    root.show_all()
    Gtk.main()
