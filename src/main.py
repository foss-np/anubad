#!/usr/bin/env python

import os, sys

filepath = os.path.abspath(__file__)
fullpath = os.path.dirname(filepath) + '/'

exec(open(fullpath + "gsettings.conf").read())
exec(open(fullpath + "mysettings.conf").read())

PATH_GLOSS = fullpath + PATH_GLOSS

if PATH_MYLIB and os.path.isdir(PATH_MYLIB):
    sys.path.append(PATH_MYLIB)
    from debugly import *

from gi.repository import Gtk, Gdk, Pango
from subprocess import Popen
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

        self.CLIP_CYCLE = None
        self.TAB_LST = []
        self.FOUND_ITEMS = []

        self.makeWidgets()
        self.connect('key_press_event', self.key_binds)


    def makeWidgets(self):
        # attach(child, left, top, width, height)
        self.attach(self.makeWidgets_toolbar(), 0, 0, 5, 1)
        self.attach(self.makeWidgets_searchbar(), 0, 1, 5, 1)
        self.attach(self.makeWidgets_sidebar(), 0, 2, 1, 2)
        self.attach(self.makeWidgets_viewer(), 1, 2, 4, 2)
        # self.attach(self.makeWidgets_settings(), 0, 3, 2, 1)
        self.attach(self.makeWidgets_browser(LIST_GLOSS[0]), 0, 4, 5, 2)


    def makeWidgets_toolbar(self):
        toolbar = Gtk.Toolbar()
        #
        ## About
        self.button_about = Gtk.ToolButton.new_from_stock(Gtk.STOCK_ABOUT)
        # button_about.connect("clicked", self.on_clear_clicked)
        toolbar.insert(self.button_about, 0)
        ##
        #
        ## # Preference
        self.button_preference = Gtk.ToolButton.new_from_stock(Gtk.STOCK_PREFERENCES)
        toolbar.insert(self.button_preference, 0)
        ##
        #
        toolbar.insert(Gtk.SeparatorToolItem(), 0)
        #
        ## Clean Viewer # overlay to cb_dropdown
        self.button_clear = Gtk.ToolButton.new_from_stock(Gtk.STOCK_CLEAR)
        toolbar.insert(self.button_clear, 0)
        self.button_clear.connect("clicked", self._clean_button)
        ##
        #
        ## Add Button
        self.button_add = Gtk.ToolButton.new_from_stock(Gtk.STOCK_ADD)
        toolbar.insert(self.button_add, 0)
        self.button_add.connect("clicked", lambda w: self.add_to_gloss())
        ##
        #
        toolbar.insert(Gtk.SeparatorToolItem(), 0)
        #
        ## Search Toggle Button
        self.toggle_search = Gtk.ToggleToolButton.new_from_stock(Gtk.STOCK_DIALOG_INFO)
        self.toggle_search.set_active(False)
        toolbar.insert(self.toggle_search, 0)
        ##
        #
        ## Smart Copy Toggle Button
        self.toggle_copy = Gtk.ToggleToolButton.new_from_stock(Gtk.STOCK_COPY)
        toolbar.insert(self.toggle_copy, 0)
        self.toggle_copy.set_active(True)
        ##
        #
        ## Spell-check Toggle Button
        self.toggle_spell = Gtk.ToggleToolButton.new_from_stock(Gtk.STOCK_SPELL_CHECK)
        toolbar.insert(self.toggle_spell, 0)
        self.toggle_spell.set_active(True)
        ##
        #
        ## Auto Transliterate Button
        self.toggle_trans = Gtk.ToggleToolButton.new_from_stock(Gtk.STOCK_CONVERT)
        toolbar.insert(self.toggle_trans, 0)
        self.toggle_trans.set_active(True)
        ##
        #
        toolbar.insert(Gtk.SeparatorToolItem(), 0)
        #
        ## Button Forward Button
        self.button_forward = Gtk.ToolButton.new_from_stock(Gtk.STOCK_GO_FORWARD)
        toolbar.insert(self.button_forward, 0)
        self.button_forward.connect("clicked", lambda e: self._forward_click())
        self.button_forward.set_sensitive(False)
        ##
        #
        ## Button Back Button
        self.button_back = Gtk.ToolButton.new_from_stock(Gtk.STOCK_GO_BACK)
        toolbar.insert(self.button_back, 0)
        self.button_forward.connect("clicked", lambda e: self._back_click())
        self.button_back.set_sensitive(False)

        return toolbar


    def _back_click(self):
        print("back clicked")
        self.button_forward.set_sensitive(True)


    def _forward_click(self):
        print("forward clicked")


    def _clean_button(self, widget):
        self.viewer.textbuffer.set_text("")
        self.cb_dropdown.clear()


    def makeWidgets_searchbar(self):
        layout = Gtk.HBox()

        label = Gtk.Label()
        label.set_markup("<b>Query</b>")
        layout.add(label)

        self.search_history = []
        self.cb_dropdown = Gtk.ListStore(str)
        self.cb_search = Gtk.ComboBox.new_with_model_and_entry(self.cb_dropdown)
        layout.add(self.cb_search)
        self.entry = self.cb_search.get_child()
        self.cb_search.set_entry_text_column(0)


        ### binding
        self.cb_search.connect('key_release_event', self.searchbar_binds)
        accel_search = Gtk.AccelGroup()
        root.add_accel_group(accel_search)
        self.cb_search.add_accelerator("grab_focus", accel_search, ord('f'), Gdk.ModifierType.CONTROL_MASK, 0)

        ## Button
        self.b_search = Gtk.Button(label="Search", stock=Gtk.STOCK_FIND)
        layout.add(self.b_search)
        self.b_search.connect('clicked', self.searchWord)

        return layout


    def searchbar_binds(self, widget, event):
        # print(event.keyval)
        if event.keyval == 65293: # <enter> return
            self.searchWord()

        if Gdk.ModifierType.CONTROL_MASK & event.state:
            if event.keyval == ord('c'):
                self.entry.set_text("")
            elif event.keyval == ord('e'):
                query = self.entry.get_text()
                current_tab = self.notebook.get_current_page()
                if not query.strip():
                    self.TAB_LST[current_tab].open_src()
                    return
                t, _id, *etc = self.FOUND_ITEMS[0] if self.FOUND_ITEMS else [ current_tab, None]
                self.TAB_LST[t].open_src(_id)


    def makeWidgets_sidebar(self):
        layout = Gtk.VBox()

        scroll = Gtk.ScrolledWindow()
        layout.add(scroll)
        scroll.set_vexpand(False)

        self.liststore = Gtk.ListStore(str)
        self.treeview = Gtk.TreeView(model=self.liststore)
        scroll.add(self.treeview)
        renderer_text = Gtk.CellRendererText()
        c0 = Gtk.TreeViewColumn("Suggestions", renderer_text, text=0)
        self.treeview.append_column(c0)
        return layout


    def makeWidgets_viewer(self):
        self.viewer = Vi.Viewer(self)
        # self.viewer.connect('key_press_event', self.viewer_binds)
        # self.viewer.textview.override_font(Pango.font_description_from_string('DejaVu Sans Mono 12'))
        self.viewer.textview.modify_font(Pango.font_description_from_string('DejaVu Sans Mono 12'))
        return self.viewer


    def makeWidgets_settings(self):
        layout = Gtk.HBox()

        self.font_button = Gtk.FontButton()
        layout.add(self.font_button)
        self.font_button.set_font_name('DejaVu Sans Mono 12')
        self.font_button.connect('font-set', lambda w: self.viewer.modify_font(w.get_font_desc()))

        # SHOW HIDE GLOSS
        #toolbar.insert(Gtk.ToolButton.new_from_stock(Gtk.STOCK_GOTO_TOP), 0)
        # toolbar.insert(Gtk.ToolButton.new_from_stock(Gtk.STOCK_GOTO_BOTTOM), 0)

        layout.add(Gtk.ToolButton.new_from_stock(Gtk.STOCK_CLOSE))
        layout.add(Gtk.ToolButton.new_from_stock(Gtk.STOCK_APPLY))

        return layout


    def makeWidgets_browser(self, gloss):
        self.GLOSS = PATH_GLOSS + gloss
        self.notebook = Gtk.Notebook()
        tab = 0
        for file_name in os.listdir(self.GLOSS):
            if not file_name[-4:] in FILE_TYPES: continue
            if "main.tra" in file_name: self.MAIN_TAB = tab
            obj = BL.BrowseList(self.parent, self.GLOSS + file_name)
            self.notebook.append_page(obj, Gtk.Label(label=file_name[:-4]))
            self.TAB_LST.append(obj)
            tab += 1
        return self.notebook


    def searchWord(self, *args):
        ## TODO: Reverse search in nepali
        # grep might be useful for quick implementation
        query = self.entry.get_text().strip().lower()
        if not query: return
        clip_out = []
        self.FOUND_ITEMS.clear()
        self.liststore.clear()
        for word in query.split():
            foundFlag = False
            for tab, obj in enumerate(self.TAB_LST):
                for item in obj.liststore:
                    if word not in item[1]: continue
                    self.liststore.append(item[1:2])
                    if word != item[1] and not self.toggle_search.get_active(): continue
                    row = [tab] + list(item)
                    clip_out += self.viewer.parser(row)
                    foundFlag = True
                    self.FOUND_ITEMS.append(row)
                    self.cb_dropdown.insert(0, [word])
            if foundFlag is False:
                self.viewer.not_found(word)

        if len(clip_out) == 0:
            self.viewer.jump_to_end()
            return

        if len(self.cb_dropdown) > 1:
            self.button_back.set_sensitive(True)

        self.viewer.mark_found(clip_out[0])
        self.CLIP_CYCLE = circle(clip_out)
        self.cb_search.grab_focus()

        if not self.toggle_copy.get_active(): return

        global clipboard, diff
        diff = 1
        curr = next(self.CLIP_CYCLE)
        clipboard.set_text(curr, -1)


    def open_dir(self):
        print(Popen(["nemo", self.GLOSS]).pid)


    def reload(self, gloss):
        if self.GLOSS == PATH_GLOSS + gloss:
            word = self.entry.get_text().strip().lower()
            xcowsay(word)
            return

        self.remove(gui.notebook)
        del gui.notebook
        for obj in self.TAB_LST:
            del obj
        self.TAB_LST.clear()

        gui.attach(gui.makeWidgets_browser(gloss), 0, 4, 5, 2)
        root.show_all()
        gui.searchWord()


    def _circular_search(self, d):
        if not self.CLIP_CYCLE:
            self.cb_search.grab_focus()
            return

        global diff
        diff = d
        text = next(self.CLIP_CYCLE)
        self.viewer.mark_found(text)
        if self.toggle_copy.get_active():
            clipboard.set_text(text, -1)


    def _circular_tab_switch(self, d):
        c = self.notebook.get_current_page()
        t = self.notebook.get_n_pages()
        n = c + d
        if n >= t: n = 0
        elif n < 0: n = t - 1
        self.notebook.set_current_page(n)


    def add_to_gloss(self, _word=""):
        _word = self.entry.get_text().strip().lower()
        win = add_window(self, word=_word)
        win.show_all()


    def key_binds(self, widget, event):
        # print(event.keyval)
        if event.keyval == 65307: Gtk.main_quit() # Esc
        elif event.keyval == 65481: self.reload(LIST_GLOSS[0]) # F12
        elif event.keyval == 65480: self.reload(LIST_GLOSS[1]) # F11
        elif event.keyval == 65479: self.reload(LIST_GLOSS[2]) # F10

        word = self.entry.get_text().strip().lower()
        if Gdk.ModifierType.CONTROL_MASK & event.state:
            if event.keyval == ord('i'): self.add_to_gloss(word)
            elif event.keyval == ord('1'): dict_grep(word)
            elif event.keyval == ord('2'): web_search(word)
            elif event.keyval == ord('o'): self.open_dir()
            elif event.keyval == ord('l'): self._clean_button(gui.viewer)
            elif event.keyval == ord('r'): self._circular_search(-1)
            elif event.keyval == ord('s'): self._circular_search(+1)
            elif event.keyval == 65365: self._circular_tab_switch(-1) # pg-down
            elif event.keyval == 65366: self._circular_tab_switch(+1) # pg-up
            elif event.keyval == ord('v'):
                text = clipboard.wait_for_text()
                self.entry.set_text(text.strip().lower())
                self.cb_search.grab_focus()
                self.searchWord()
            return

        if Gdk.ModifierType.META_MASK and event.state:
            if ord('1') <= event.keyval <= ord('9'):
                t = event.keyval - ord('1')
                self.notebook.set_current_page(t) # NOTE: range check not needed
            elif event.keyval == ord('0'):
                self.notebook.set_current_page(self.MAIN_TAB)


class add_window(Gtk.Window):
    def __init__(self, parent=None, word=""):
        Gtk.Window.__init__(self)
        self.parent = parent
        self.word = word

        self.makeWidgets()
        self.connect('key_press_event', self.key_binds)

    def makeWidgets(self):
        layout = Gtk.Grid()
        layout.set_row_spacing(5)
        layout.set_column_spacing(5)

        self.add(layout)

        label = Gtk.Label()
        layout.attach(label, 0, 0, 1, 1)
        label.set_markup("<b>lang_1</b>")

        self.lang1 = Gtk.Entry()
        layout.attach(self.lang1, 1, 0, 1, 1)
        self.lang1.set_text(self.word)
        # self.lang1.grab_focus()

        label = Gtk.Label()
        layout.attach(label, 0, 1, 1, 1)
        label.set_markup("<b>lang_2</b>")

        self.lang2 = Gtk.Entry()
        layout.attach(self.lang2, 1, 1, 1, 1)

        label = Gtk.Label()
        layout.attach(label, 0, 2, 1, 1)
        label.set_markup("<b>file</b>")

        self.gloss_file = Gtk.ComboBoxText()
        layout.attach(self.gloss_file, 1, 2, 1, 1)
        for obj in self.parent.TAB_LST:
            *a, label = obj.SRC.split('/')
            self.gloss_file.append_text(label)
        self.gloss_file.set_active(self.parent.notebook.get_current_page())

        self.button_cancel = Gtk.Button(label="Cancel")
        layout.attach(self.button_cancel, 0, 3, 1, 1)
        self.button_cancel.connect("clicked", lambda e: self.destroy())

        self.button_add = Gtk.Button(label="Add")
        layout.attach(self.button_add, 1, 3, 1, 1)
        self.button_add.connect("clicked", self._add_button)


    def _add_button(self, widget):
        row = [ self.lang1.get_text().strip().lower() ]
        row.append(self.lang2.get_text().strip())

        if not (row[0] and row[1]):
            self.lang1.grab_focus()
            return


        obj = self.parent.TAB_LST[self.gloss_file.get_active()]
        fp = open(obj.SRC, 'a').write("\n" + '; '.join(row))
        count = obj.add_to_tree(row)
        self.parent.viewer.parser([0, count] + row)
        self.destroy()


    def key_binds(self, widget, event):
        # print(event.keyval)
        if event.keyval == 65307: self.destroy() # Esc


diff = 1
def circle(iterable):
    saved = iterable[:]
    i = -1
    global diff
    while saved:
        l = len(saved)
        i += diff
        if diff == 1 and l <= i: i = 0
        if diff == -1 and i < 0: i = l - 1
        yield saved[i]


def main():
    global root
    root = Gtk.Window(title="anubad - अनुवाद")
    root.connect('delete-event', Gtk.main_quit)
    root.set_default_size(600, 500)

    global gui
    gui = GUI(root)
    gui.cb_search.grab_focus()
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
    # NOTE: GTK BUG, notebook page switch only after its visible
    gui.notebook.set_current_page(gui.MAIN_TAB)
    Gtk.main()
