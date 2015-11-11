#!/usr/bin/env python3

import os, sys
from subprocess import Popen

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Pango

import core

class Table(Gtk.Overlay):
    def __init__(self, parent=None, lstore=None):
        Gtk.Overlay.__init__(self)
        if lstore is None:
            print("lstore can't be None")
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


class Notebook(Gtk.Notebook):
    def __init__(self, gloss, parent=None):
        Gtk.Notebook.__init__(self)
        self.parent = parent
        self.gloss = gloss
        self.track_FONT = set()

        self.MAIN_TAB = 0

        self.makeWidgets()
        self.set_scrollable(True)
        self.show_all()
        # NOTE: GTK BUG, notebook page switch only after its visible
        self.set_current_page(self.MAIN_TAB)


    def makeWidgets(self, gloss=None):
        if gloss is None:
            gloss = self.gloss

        for i, (name, (lstore, invert, path)) in enumerate(gloss.categories.items()):
            if "main" == name: self.MAIN_TAB = i
            obj = Table(self.parent, lstore)
            obj.treeview.connect("row-activated", self.browser_row_double_click)
            obj.treeview.modify_font(FONT_obj)
            self.track_FONT.add(obj.treeview)
            self.append_page(obj, Gtk.Label(label=name))


    def _circular_tab_switch(self, diff=1):
        current = self.get_current_page()
        total = self.get_n_pages()
        new = current + diff
        if new >= total: new = 0
        elif new < 0: new = total - 1
        self.set_current_page(new)


    def browser_row_double_click(self, widget, treepath, treeviewcol):
        selection = widget.get_selection()
        model, treeiter = selection.get_selected()

        if treeiter is None: return
        tab = self.get_current_page()
        obj = self.get_nth_page(tab)
        ID, word, info = model[treeiter]

        # self.viewer.parse(row, obj.SRC)
        parsed_info = core.Glossary.format_parser(info)
        self.parent.viewer.append_result(word, parsed_info, "gloss/demo")
        self.parent.viewer.jump_to_end()


    def key_binds(self, widget, event):
        keyval, state = event.keyval, event.state
        # elif keyval == 65474: self._reload_gloss() # F5
        if keyval == 65307:  Gtk.main_quit()
        if Gdk.ModifierType.CONTROL_MASK & state:
            if   keyval == 65365: self._circular_tab_switch(-1) # Pg-Dn
            elif keyval == 65366: self._circular_tab_switch(+1) # Pg-Up
        elif Gdk.ModifierType.MOD1_MASK & state:
            if ord('1') <= keyval <= ord('9'): self.set_current_page(keyval - ord('1')) # NOTE: range check not needed
            elif keyval == ord('0'): self.set_current_page(self.MAIN_TAB)

        # if event.keyval in ignore_keys: return


def main():
    global PATH_GLOSS
    core.PATH_GLOSS = PATH_GLOSS = PATH_GLOSS

    # global ignore_keys
    # ignore_keys = [ v for k, v in utils.key_codes.items() if v != utils.key_codes["RETURN"]]

    for path in LIST_GLOSS:
        core.Glossary(path)

    root = Gtk.Window()
    root.connect('delete-event', Gtk.main_quit)
    root.set_default_size(600, 300)

    global FONT_obj
    FONT_obj = Pango.font_description_from_string(def_FONT)

    notebook = Notebook(core.Glossary.instances[0])
    root.add(notebook)
    root.connect('key_release_event', notebook.key_binds)
    return root


if __name__ == '__main__':
    exec(open("gsettings.conf", encoding="UTF-8").read())
    # import utils
    fp3 = sys.stdout
    core.fp3 = fp3

    root = main()
    root.show_all()
    Gtk.main()
