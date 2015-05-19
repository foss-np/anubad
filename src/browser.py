#!/usr/bin/env python

import os, sys
from subprocess import Popen
from gi.repository import Gtk, Gdk, Pango

class BrowseList(Gtk.Overlay):
    def __init__(self, parent=None, src=None):
        Gtk.Overlay.__init__(self)
        self.SRC = src
        self.makeWidgets()

        if self.SRC:
            self.fill_tree(src)


    def makeWidgets(self):
        self.scroll = Gtk.ScrolledWindow()
        self.add(self.scroll)
        self.scroll.set_hexpand(True)
        self.scroll.set_vexpand(True)

        self.tool_b_Refresh = Gtk.ToolButton(icon_name=Gtk.STOCK_REFRESH)
        self.add_overlay(self.tool_b_Refresh)
        self.tool_b_Refresh.connect("clicked", lambda *a: self.reload())
        self.tool_b_Refresh.set_valign(Gtk.Align.START)
        self.tool_b_Refresh.set_halign(Gtk.Align.END)

        self.treebuffer = Gtk.ListStore(int, str, str)
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


    def fill_tree(self, src):
        """
        >>> exec(open("mysettings.conf").read())
        >>> obj = BrowseList(root)
        >>> root.add(obj)
        >>> obj.fill_tree(PATH_GLOSS + LIST_GLOSS[0] + "main.tra")
        loading: *../gloss/foss_gloss/en2np/main.tra
        """

        print("loading: *" + src[-40:], file=fp3)
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


    def reload(self):
        print("reload:", self.SRC[-30:], file=sys.stderr)
        self.treebuffer.clear()
        self.fill_tree(self.SRC)


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
    fp3 = open(os.devnull, 'w')

    import doctest
    doctest.testmod()
    root.show_all()
    Gtk.main()
