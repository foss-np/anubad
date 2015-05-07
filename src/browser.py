#!/usr/bin/env python

import os
from subprocess import Popen
from gi.repository import Gtk, Gdk, Pango

class BrowseList(Gtk.ScrolledWindow):
    def __init__(self, parent=None, src=None):
        Gtk.ScrolledWindow.__init__(self)
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.SRC = src
        self.makeWidgets()

        if self.SRC:
            self.fill_tree(src)


    def makeWidgets(self):
        #
        ## Setting
        ## TODO: PUT THE LOCK ICON

        self.treebuffer = Gtk.ListStore(int, str, str)
        self.treeview = Gtk.TreeView(model=self.treebuffer)
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
        self.treebuffer[path][2] = text


    def fill_tree(self, src):
        """
        >>> exec(open("mysettings.conf").read())
        >>> obj = BrowseList(root)
        >>> root.add(obj)
        >>> obj.fill_tree(PATH_GLOSS + LIST_GLOSS[0] + "main.tra")
        loading: *../gloss/foss_gloss/en2np/main.tra
        """

        print("loading: *" + src[-40:])
        data = open(src, encoding="UTF-8").read()
        self.count = 0

        for line in data.splitlines():
            self.count += 1
            row = line.split('; ')
            if len(row) != 2:
                # TODO: open leafpad automatically with the current error line
                print("File Format Error: %s: %d"%(self.SRC, self.count))
                arg = "--jump=%d"%self.count
                # NOTE: we need something to hang on till we edit
                ## print("pid:", Popen(["leafpad", arg, self.SRC]).pid)
                ## DONT USES Popen ^^^^
                os.system("setsid leafpad %s %s"%(arg, self.SRC))
                exit(1)
            row.insert(0, self.count)
            self.treebuffer.append(row)


    def add_to_tree(self, row):
        self.count += 1
        self.treebuffer.append([self.count] + row)
        return self.count


    def open_src(self, ID=None):
        # TODO : smart xdg-open with arguments
        # if not self.CURRENT_FOUND_ITEM:
        #     open_src()
        #     return
        if ID:
            arg = "--jump=%d"%ID
            print("pid:", Popen(["leafpad", arg, self.SRC]).pid)
        else:
            print("pid:", Popen(["leafpad", self.SRC]).pid)


def root_binds(widget, event):
    # print(event.keyval)
    if event.keyval == 65307:
        Gtk.main_quit()


def main():
    global root
    root = Gtk.Window()
    root.connect('delete-event', Gtk.main_quit)
    root.connect('key_release_event', root_binds)
    root.set_default_size(600, 300)


if __name__ == '__main__':
    main()
    import doctest
    doctest.testmod()
    root.show_all()
    Gtk.main()
