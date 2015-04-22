#!/usr/bin/env python

import os, sys

filepath = os.path.abspath(__file__)
fullpath = os.path.dirname(filepath) + '/'

exec(open(fullpath + "gsettings.conf").read())
exec(open(fullpath + "mysettings.conf").read())

PATH_GLOSS = fullpath + PATH_GLOSS + '/'

if PATH_MYLIB:
    sys.path.append(PATH_MYLIB)
    from debugly import *

from gi.repository import Gtk, Gdk, Pango
import browselst2 as BL
import viewer2 as Vi

#   ____ _   _ ___
#  / ___| | | |_ _|
# | |  _| | | || |
# | |_| | |_| || |
#  \____|\___/|___|

class GUI(Gtk.Grid):
    def __init__(self, parent=None):
        Gtk.Grid.__init__(self)
        self.parent = parent

        self.makeWidgets()

    def makeWidgets(self):
        # self.attach(self.makeWidgets_sidebar(), 0, 0, 1, 2)
        self.attach(self.makeWidgets_searchbar(), 1, 0, 1, 1)
        self.attach(self.makeWidgets_viewer(), 1, 1, 1, 1)

        ## browser
        self.browser = BL.BrowseList(self.parent, PATH_GLOSS + LIST_GLOSS[0])
        self.attach(self.browser, 0, 2, 2, 1)


    def makeWidgets_sidebar(self):
        f_sidebar = Gtk.VBox()

        self.gloss_list = Gtk.ListStore(str)
        countries = ["Austria", "Brazil", "Belgium", "France", "Germany",
                     "Switzerland", "United Kingdom", "United States of America",
                     "Uruguay"]
        for country in countries:
            self.gloss_list.append([country])

        # self.cb_gloss = Gtk.ComboBox(model=self.gloss_list)
        # f_sidebar.add(self.cb_gloss)

        scroll = Gtk.ScrolledWindow()
        f_sidebar.add(scroll)
        scroll.set_vexpand(False)

        self.liststore = Gtk.ListStore(str)
        self.treeview = Gtk.TreeView(model=self.liststore)
        scroll.add(self.treeview)
        renderer_text = Gtk.CellRendererText()
        c0 = Gtk.TreeViewColumn("Suggestions", renderer_text, text=0)
        self.treeview.append_column(c0)
        self.liststore.append(["hello"])
        self.liststore.append(["world"])

        return f_sidebar


    def makeWidgets_viewer(self):
        layout = Gtk.VBox()

        self.textview = Vi.Viewer(self)
        layout.add(self.textview)
        # self.textview.override_font(Pango.font_description_from_string('DejaVu Sans Mono 12'))
        self.textview.modify_font(Pango.font_description_from_string('DejaVu Sans Mono 12'))

        # self.font_button = Gtk.FontButton()
        # f_viewer.add(self.font_button)
        # self.font_button.set_font_name('DejaVu Sans Mono 12')
        # self.font_button.connect('font-set', lambda w: self.textview.modify_font(w.get_font_desc()))

        return layout


    def makeWidgets_searchbar(self):
        layout = Gtk.HBox()

        label = Gtk.Label("Query")
        layout.add(label)

        #self.cb_search.set_icon_from_stock(Gtk.EntryIconPosition.PRIMARY, Gtk.STOCK_FIND)

        self.search_history = Gtk.ListStore(int, str)
        self.cb_search = Gtk.ComboBox.new_with_model_and_entry(self.search_history)
        self.cb_search.set_entry_text_column(1)
        layout.add(self.cb_search)

        # button_clear = Gtk.ToolButton.new_from_stock(Gtk.STOCK_CLEAR)
        # button_clear.connect("clicked", self.on_clear_clicked)
        # toolbar.insert(button_clear, 9)

        ### binding
        self.cb_search.connect('key_release_event', self.cb_binds)
        accel_search = Gtk.AccelGroup()
        root.add_accel_group(accel_search)
        self.cb_search.add_accelerator("grab_focus", accel_search, ord('f'), Gdk.ModifierType.CONTROL_MASK, 0)
        self.cb_search.add_accelerator("grab_focus", accel_search, ord('l'), Gdk.ModifierType.CONTROL_MASK, 0)
        self.cb_search.add_accelerator("grab_focus", accel_search, ord('v'), Gdk.ModifierType.CONTROL_MASK, 0)

        ## Button
        self.b_search = Gtk.Button(label="Search")
        layout.add(self.b_search)
        self.b_search.connect('clicked', self.searchWord)

        return layout


    def cb_binds(self, widget, event):
        # print(event.keyval)
        if event.keyval == 65293:
            self.searchWord()

    def searchWord(self):
        entry = self.cb_search.get_child()
        text = entry.get_text().strip().lower()
        if not text: return
        out = []

        for val in text.split():
            foundFlag = False
            tab = 0
            for item in self.browser.liststore:
                if item[1] != val : continue
                out += self.textview.parser([tab] + list(item))
                foundFlag = True
                break

            if foundFlag is False:
                self.textview.not_found(val)
                return

        global clipboard
        clipboard.set_text(out[0], -1)
        self.CURRENT_FOUND_ITEM = item


def add_to_gloss(parent):
    entry = gui.cb_search.get_child()
    word = entry.get_text().strip().lower()

    dialogWindow = Gtk.MessageDialog(parent,
                                     Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                     Gtk.MessageType.QUESTION,
                                     Gtk.ButtonsType.OK_CANCEL,
                                     "translate of '%s'"%word)
    dialogWindow.set_title("Add to gloss")

    dialogBox = dialogWindow.get_content_area()
    userEntry = Gtk.Entry()
    # userEntry.set_visibility(True)
    userEntry.set_size_request(250,0)
    dialogBox.pack_end(userEntry, False, False, 0)

    dialogWindow.show_all()

    response = dialogWindow.run()
    text = userEntry.get_text()
    dialogWindow.destroy()

    if response != Gtk.ResponseType.OK or text == '':
        return None

    row = [word, text]
    obj = gui.browser
    fp = open(obj.GLOSS, 'a').write("\n" + '; '.join(row))
    gui.browser.add_to_tree(row)


def on_key_press(widget, event):
    # print(event.keyval)
    if event.keyval == 65307: Gtk.main_quit()
    elif event.keyval == 65481: reload(LIST_GLOSS[0]) #F12
    elif event.keyval == 65480: reload(LIST_GLOSS[1]) #F11
    elif event.keyval == 65479: reload(LIST_GLOSS[2]) #F10

    if Gdk.ModifierType.CONTROL_MASK & event.state:
        if event.keyval == ord('c'):
            entry = gui.cb_search.get_child()
            entry.set_text("")
        elif event.keyval == ord('i'): add_to_gloss(root)
        elif event.keyval == ord('t'): dict_grep()
        elif event.keyval == ord('v'):
            global clipboard
            text = clipboard.wait_for_text()
            entry = gui.cb_search.get_child()
            entry.set_text(text.strip().lower())
            gui.searchWord()
        elif event.keyval == ord('o'):
            ID = 0
            if gui.CURRENT_FOUND_ITEM:
                ID = gui.CURRENT_FOUND_ITEM[0]
            gui.browser.open_dir()
        elif event.keyval == ord('u'):
            ID = 0
            if gui.CURRENT_FOUND_ITEM:
                ID = gui.CURRENT_FOUND_ITEM[0]
            gui.browser.open_gloss(ID)


def reload(gloss):
    if not gloss: return
    if gui.browser.GLOSS == PATH_GLOSS + gloss: return

    print("loading:", "gloss/" + gloss)
    gui.remove(gui.browser)
    del gui.browser
    gui.browser = BL.BrowseList(gui.parent, PATH_GLOSS + gloss)
    gui.attach(gui.browser, 0, 2, 2, 1)
    root.show_all()

    gui.searchWord()


def main():
    global root
    root = Gtk.Window(title="anubad - अनुवाद")
    root.connect('delete-event', Gtk.main_quit)
    root.connect('key_release_event', on_key_press)
    root.set_default_size(600, 500)

    global gui
    gui = GUI(root)
    root.add(gui)

    global clipboard
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

if __name__ == '__main__':
    main()
    if PATH_PLUGINS:
        # TODO: trasliterate, espeak
        PATH_PLUGINS = fullpath + PATH_PLUGINS + '/'
        for file_name in os.listdir(PATH_PLUGINS):
            print("plugin:", file_name)
            exec(open(PATH_PLUGINS + file_name).read())
    root.show_all()
    Gtk.main()
