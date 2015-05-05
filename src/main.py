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
    from pprint import pprint

from gi.repository import Gtk, Gdk, Pango
from subprocess import Popen
import browser as BL
import viewer as Vi
from add import Add

#   ____ _   _ ___
#  / ___| | | |_ _|
# | |  _| | | || |
# | |_| | |_| || |
#  \____|\___/|___|

class GUI(Gtk.Window):
    def __init__(self, parent=None):
        Gtk.Window.__init__(self, title="anubad - अनुवाद")
        self.set_default_size(600, 500)

        self.parent = parent

        self.CLIP_CYCLE = None
        self.TAB_LST = []
        self.FOUND_ITEMS = []
        self.VIEWED_ITEMS = set()
        self.CURRENT_VIEW = None

        self.lets_add = None

        self.makeWidgets()
        self.connect('key_press_event', self.key_binds)
        self.cb_search.grab_focus()
        self.show_all()
        # NOTE: GTK BUG, notebook page switch only after its visible
        self.notebook.set_current_page(self.MAIN_TAB)


    def makeWidgets(self):
        self.layout = Gtk.Grid()
        self.add(self.layout)

        # attach(child, left, top, width, height)
        self.layout.attach(self.makeWidgets_toolbar(), 0, 0, 5, 1)
        self.layout.attach(self.makeWidgets_searchbar(), 0, 1, 5, 1)
        self.layout.attach(self.makeWidgets_sidebar(), 0, 2, 1, 2)
        self.layout.attach(self.makeWidgets_viewer(), 1, 2, 4, 2)
        self.layout.attach(self.makeWidgets_settings(), 0, 4, 5, 1)
        self.layout.attach(self.makeWidgets_browser(LIST_GLOSS[0]), 0, 5, 5, 2)


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
        self.VIEWED_ITEMS.clear()
        self.viewer.textbuffer.set_text("")
        self.cb_dropdown.clear()
        self.cb_search.grab_focus()


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
        self.add_accel_group(accel_search)
        self.cb_search.add_accelerator("grab_focus", accel_search, ord('f'), Gdk.ModifierType.CONTROL_MASK, 0)

        ## Button
        self.b_search = Gtk.Button(label="Search", stock=Gtk.STOCK_FIND)
        layout.add(self.b_search)
        self.b_search.connect('clicked', lambda w: self.searchbar_binds(w, None))

        return layout


    def searchbar_binds(self, widget, event):
        # print(event.keyval)
        query = self.entry.get_text().strip().lower()
        if event is None:
            self.searchWord(query)
        elif Gdk.ModifierType.CONTROL_MASK & event.state:
            if event.keyval == ord('c'):
                self.entry.set_text("")
        elif Gdk.ModifierType.SHIFT_MASK & event.state:
            if event.keyval == 65293: # <enter> return
                state = self.toggle_search.get_active()
                self.toggle_search.set_active(not state)
                self.searchWord(query)
                self.toggle_search.set_active(state)
        elif event.keyval == 65293: # <enter> return
            self.searchWord(query)


    def makeWidgets_sidebar(self):
        layout = Gtk.VBox()

        scroll = Gtk.ScrolledWindow()
        layout.add(scroll)
        scroll.set_vexpand(False)

        self.suggestions = Gtk.ListStore(int, str)
        self.treeview = Gtk.TreeView(model=self.suggestions)
        scroll.add(self.treeview)
        renderer_text = Gtk.CellRendererText()
        self.treeview.append_column(Gtk.TreeViewColumn("#", renderer_text, text=0))
        self.treeview.append_column(Gtk.TreeViewColumn("Suggestions", renderer_text, text=1))
        select = self.treeview.get_selection()
        select.connect("changed", self.on_sidebar_selection)
        return layout


    def on_sidebar_selection(self, selection):
        if not self.FOUND_ITEMS: return

        model, treeiter = selection.get_selected()
        if treeiter is None: return
        i = model[treeiter][0] - 1
        self.CURRENT_VIEW = i
        p = i not in self.VIEWED_ITEMS
        tab, *row = self.FOUND_ITEMS[i]
        clip_out = self.viewer.parse(tab, self.TAB_LST[tab], row, _print=p)
        self.CLIP_CYCLE = circle(clip_out)
        self._circular_search(+1)


    def makeWidgets_viewer(self):
        self.viewer = Vi.Viewer(self)
        # self.viewer.connect('key_press_event', self.viewer_binds)
        # self.viewer.textview.override_font(Pango.font_description_from_string('DejaVu Sans Mono 12'))
        self.viewer.textview.modify_font(Pango.font_description_from_string(def_FONT))
        self.viewer.connect('key_press_event', self.viewer_binds)
        return self.viewer


    def viewer_binds(self, widget, event):
        # print(event.keyval)
        # TODO: TESTING: not working properly
        if event.keyval and self.viewer.toggle_edit.get_active():
            self.cb_search.grab_focus()
            self.searchbar_binds(widget, event)


    def makeWidgets_settings(self):
        layout = Gtk.HBox()

        self.font_button = Gtk.FontButton()
        layout.add(self.font_button)
        self.font_button.set_font_name(def_FONT)
        self.font_button.connect('font-set', self._change_font)

        # SHOW HIDE GLOSS
        # toolbar.insert(Gtk.ToolButton.new_from_stock(Gtk.STOCK_GOTO_TOP), 0)
        # toolbar.insert(Gtk.ToolButton.new_from_stock(Gtk.STOCK_GOTO_BOTTOM), 0)
        # layout.add(Gtk.ToolButton.new_from_stock(Gtk.STOCK_CLOSE))
        # layout.add(Gtk.ToolButton.new_from_stock(Gtk.STOCK_APPLY))
        return layout


    def _change_font(self, widget):
        f_obj = widget.get_font_desc()
        self.viewer.textview.modify_font(f_obj)
        ff, fs = f_obj.get_family(), int(f_obj.get_size()/1000)
        font = ff + ' ' + str(fs)
        conf = open("mysettings.conf").read()
        global def_FONT
        nconf = conf.replace(def_FONT, font)
        open("mysettings.conf", 'w').write(nconf)
        def_FONT = font


    def makeWidgets_browser(self, gloss):
        self.GLOSS = PATH_GLOSS + gloss
        self.notebook = Gtk.Notebook()
        tab = 0
        for file_name in os.listdir(self.GLOSS):
            if not file_name[-4:] in FILE_TYPES: continue
            if "main.tra" in file_name: self.MAIN_TAB = tab
            obj = BL.BrowseList(self.parent, self.GLOSS + file_name)

            # TODO font change
            # font = Pango.FontDescription(def_FONT)
            # obj.renderer_text.cell.set_property('font-desc', font)

            self.notebook.append_page(obj, Gtk.Label(label=file_name[:-4]))
            self.TAB_LST.append(obj)
            tab += 1
        return self.notebook


    def searchWord(self, query):
        ## TODO: Reverse search in nepali
        # grep might be useful for quick implementation
        if not query: return
        clip_out = []
        self.FOUND_ITEMS.clear()
        self.suggestions.clear()
        self.VIEWED_ITEMS.clear()
        self.CURRENT_VIEW = None
        found = 0
        for word in set(query.split()):
            foundFlag = False
            for tab, obj in enumerate(self.TAB_LST):
                # TODO: make it simpler
                # MAYBE: put the tree search in browserlst itself
                for item in obj.treebuffer:
                    if word not in item[1]: continue
                    # self.treeview.row_activated(0, self.suggestions)
                    # NOTE: may be use interator counter
                    found += 1
                    row = [tab] + list(item)
                    if row not in self.FOUND_ITEMS: # remove duplicate longest str match
                        self.FOUND_ITEMS.append(row)
                        self.suggestions.append([found, item[1]])
                    if word != item[1] and not self.toggle_search.get_active(): continue
                    self.cb_dropdown.insert(0, [word])
                    clip_out += self.viewer.parse(tab, obj, row[1:])
                    self.CURRENT_VIEW = found - 1
                    self.VIEWED_ITEMS.add(self.CURRENT_VIEW)
                    foundFlag = True
            if foundFlag is False:
                self.viewer.not_found(word)

        if len(clip_out) == 0: return


        if len(self.cb_dropdown) > 1:
            self.button_back.set_sensitive(True)

        self.cb_search.grab_focus()
        self.CLIP_CYCLE = circle(clip_out)


        if self.toggle_copy.get_active():
            self._circular_search(+1)


    def open_dir(self):
        print("pid:", Popen(["nemo", self.GLOSS]).pid)


    def open_term(self):
        print("pid:", Popen([TERMINAL, "--working-directory=%s"%self.GLOSS]).pid)


    def reload(self, gloss):
        query = self.entry.get_text().strip().lower()
        if self.GLOSS == PATH_GLOSS + gloss:
            xcowsay(query)
            return

        self.layout.remove(self.notebook)
        del self.notebook
        for obj in self.TAB_LST:
            del obj
        self.TAB_LST.clear()

        self.layout.attach(self.makeWidgets_browser(gloss), 0, 5, 5, 2)
        self.show_all()
        self.notebook.set_current_page(self.MAIN_TAB)
        self.searchWord(query)


    def reload_gloss(self):
        current_tab = self.notebook.get_current_page()
        obj = self.TAB_LST[current_tab]
        obj.treebuffer.clear()
        obj.fill_tree(obj.SRC)


    def _circular_search(self, d):
        if not self.CLIP_CYCLE:
            self.cb_search.grab_focus()
            return

        global diff, clipboard
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


    def add_to_gloss(self, query):
        _l2 = self.lets_add.strip() if self.lets_add else ""
        add = Add(self, l1=query, l2=_l2)


    def key_binds(self, widget, event):
        # print(event.keyval)
        if event.keyval == 65307: Gtk.main_quit() # Esc
        elif event.keyval == 65481: self.reload(LIST_GLOSS[0]) # F12
        elif event.keyval == 65480: self.reload(LIST_GLOSS[1]) # F11
        elif event.keyval == 65479: self.reload(LIST_GLOSS[2]) # F10
        elif event.keyval == 65474: self.reload_gloss() # F5

        global clipboard
        query = self.entry.get_text().strip().lower()
        if Gdk.ModifierType.CONTROL_MASK & event.state:
            if event.keyval == ord('i'): self.add_to_gloss(query)
            elif event.keyval == ord('1'): dict_grep(query, self.viewer, False)
            elif event.keyval == ord('2'): web_search(query, self.viewer)
            elif event.keyval == ord('3'): dict_grep(query, self.viewer)
            elif event.keyval == ord('o'): self.open_dir()
            elif event.keyval == ord('t'): self.open_term()
            elif event.keyval == ord('l'): self._clean_button(self.viewer)
            elif event.keyval == ord('r'): self._circular_search(-1)
            elif event.keyval == ord('s'): self._circular_search(+1)
            elif event.keyval == 65365: self._circular_tab_switch(-1) # pg-down
            elif event.keyval == 65366: self._circular_tab_switch(+1) # pg-up
            elif event.keyval == ord('g'): # grab clipboard
                text = clipboard.wait_for_text()
                self.entry.set_text(text.strip().lower())
                self.cb_search.grab_focus()
                self.searchWord(query)
            elif event.keyval == ord('e'):
                if self.CURRENT_VIEW is None: return
                t, _id, *etc = self.FOUND_ITEMS[self.CURRENT_VIEW]
                self.TAB_LST[t].open_src(_id)
            return

        if Gdk.ModifierType.META_MASK and event.state:
            if ord('1') <= event.keyval <= ord('9'):
                t = event.keyval - ord('1')
                self.notebook.set_current_page(t) # NOTE: range check not needed
            elif event.keyval == ord('0'):
                self.notebook.set_current_page(self.MAIN_TAB)


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


def root_binds(widget, event):
    # print(event.keyval)
    if event.keyval == 65307:
        Gtk.main_quit()


def main():
    global root
    root = GUI()
    root.connect('delete-event', Gtk.main_quit)

    global clipboard
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

    return root


if __name__ == '__main__':
    main().connect('key_press_event', root_binds)
    global PATH_PLUGINS
    PATH_PLUGINS = fullpath + PATH_PLUGINS
    if PATH_PLUGINS and os.path.isdir(PATH_PLUGINS):
        for file_name in os.listdir(PATH_PLUGINS):
            print("plugin:", file_name)
            exec(open(PATH_PLUGINS + file_name).read())
    Gtk.main()
