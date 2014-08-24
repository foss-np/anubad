#!/usr/bin/env python

import os

filepath = os.path.abspath(__file__)
fullpath = os.path.dirname(filepath)

exec(open(fullpath+"/settings.conf").read())
PATH_GLOSS = fullpath+PATH_GLOSS

from gi.repository import Gtk, Pango

class List_view(Gtk.ScrolledWindow):
    def __init__(self, gloss, parent=None):
        self.GLOSS = gloss

        Gtk.ScrolledWindow.__init__(self)
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.liststore = Gtk.ListStore(int, str, str)
        self.makeWidgets()
        self.fill_tree(gloss)

    def makeWidgets(self):
        self.treeview = Gtk.TreeView(model=self.liststore)
        self.add(self.treeview)

        renderer_text = Gtk.CellRendererText()
        c0 = Gtk.TreeViewColumn("#", renderer_text, text=0)
        self.treeview.append_column(c0)

        c1 = Gtk.TreeViewColumn("English", renderer_text, text=1)
        self.treeview.append_column(c1)

        renderer_editabletext = Gtk.CellRendererText()
        renderer_editabletext.set_property("editable", True)

        c2 = Gtk.TreeViewColumn("नेपाली", renderer_editabletext, text=2)
        self.treeview.append_column(c2)

        renderer_editabletext.connect("edited", self.text_edited)

    def text_edited(self, widget, path, text):
        self.liststore[path][2] = text

    def fill_tree(self, gloss):
        data = open(self.GLOSS, encoding="UTF-8").read().splitlines()
        self.count = 0

        for line in data:
            self.count += 1
            row = line.split('; ')
            if len(row) != 2:
                print("File Format Error: %s: %d"%(self.GLOSS, self.count))
                exit(1)
            row.insert(0, self.count)
            self.liststore.append(row)

class GUI():
    def __init__(self, parent=None):
        self.parent = parent
        self.makeWidgets()

    def makeWidgets(self, ):
        layout = Gtk.Grid()
        self.parent.add(layout)

        ## Combo box
        self.search_history = Gtk.ListStore(int, str)
        self.cb_search = Gtk.ComboBox.new_with_model_and_entry(self.search_history)
        self.cb_search.connect('key_release_event', self.cb_bind_enter)
        self.cb_search.set_entry_text_column(1)
        layout.add(self.cb_search)#, 0, 0, 2, 1)

        self.b_search = Gtk.Button(label="Search")
        self.b_search.connect("clicked", self.searchWord)
        layout.attach(self.b_search, 1, 0, 1, 1)

        ## Viewer
        scrolledwindow = Gtk.ScrolledWindow()
        scrolledwindow.set_hexpand(True)
        scrolledwindow.set_vexpand(True)
        layout.attach(scrolledwindow, 0, 1, 2, 2)

        self.textview = Gtk.TextView()
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD)

        self.textbuffer = self.textview.get_buffer()
        self.textbuffer.set_text("Type Something to Search")
        scrolledwindow.add(self.textview)

        self.tag_bold = self.textbuffer.create_tag("bold",  weight=Pango.Weight.BOLD)
        self.tag_italic = self.textbuffer.create_tag("italic", style=Pango.Style.ITALIC)
        self.tag_underline = self.textbuffer.create_tag("underline",  underline=Pango.Underline.SINGLE)
        self.tag_found = self.textbuffer.create_tag("found",  background="yellow")

        # # tree-viewer
        # for i, f in enumerate(os.listdir(PATH_GLOSS)):
        #     #if not f[-4:] in FILE_TYPES: continue
        self.lview = List_view(PATH_GLOSS+'main.tra', self.parent)
        layout.attach(self.lview, 0, 3, 2, 1)

    def cb_bind_enter(self, widget, event):
        # print(event.keyval)
        if event.keyval == 65293:
            self.searchWord(widget, event)

    def searchWord(self, widget, event):
        entry = self.cb_search.get_child()
        print("Entered: %s" % entry.get_text())

        # print(self.lview.liststore.iter_next(0))
        # help(self.lview.liststore.get_data)
        # print(self.lview.liststore.get_data)
        # print(dir(self.lview.liststore))


def on_key_press(widget, event):
    # print(event.keyval)
    if event.keyval == 65307:
        Gtk.main_quit()

def main():
    global gui
    win = Gtk.Window()
    win.connect('delete-event', Gtk.main_quit)
    win.connect('key_release_event', on_key_press)
    win.set_default_size(600, 500)

    gui = GUI(win)

    win.show_all()
    Gtk.main()

if __name__ == '__main__':
    main()
