#!/usr/bin/env python

PKG_NAME = "anubad - अनुवाद"

import os, sys

filepath = os.path.abspath(__file__)
fullpath = os.path.dirname(filepath) + '/'

exec(open(fullpath + "gsettings.conf").read())
exec(open(fullpath + "mysettings.conf").read())

PATH_GLOSS = fullpath + PATH_GLOSS

fp_dev_null = open(os.devnull, 'w')

if PATH_MYLIB and os.path.isdir(PATH_MYLIB):
    sys.path.append(PATH_MYLIB)
    from debugly import *
    from pprint import pprint
else:
    sys.stdout = fp_dev_null

from gi.repository import Gtk, Gdk, Pango
from subprocess import Popen
import utils
import browser as BL
import viewer as Vi
import add as Ad

#   ____ _   _ ___
#  / ___| | | |_ _|
# | |  _| | | || |
# | |_| | |_| || |
#  \____|\___/|___|
#

class GUI(Gtk.Window):
    NOTEBOOK_OBJ = []
    def __init__(self, parent=None):
        Gtk.Window.__init__(self, title=PKG_NAME)
        self.set_default_size(600, 500)

        self.parent = parent

        self.CLIP_CYCLE = None
        self.TAB_LST = []
        self.FOUND_ITEMS = []
        self.VIEWED_ITEMS = set()
        self.CURRENT_VIEW = None

        self.lets_add = None
        self.search_history = []

        self.makeWidgets()
        self.connect('key_press_event', self.key_binds)
        self.search_entry.grab_focus()
        self.show_all()
        # NOTE: GTK BUG, notebook page switch only after its visible
        self.notebook.set_current_page(self.MAIN_TAB)


    def makeWidgets(self):
        self.layout = Gtk.Grid()
        self.add(self.layout)

        self.layout.attach(self.makeWidgets_toolbar(), left=0, top=0, width=5, height=1)
        self.layout.attach(self.makeWidgets_searchbar(), 0, 1, 5, 1)

        hpaned = Gtk.Paned()
        self.layout.attach(hpaned, 0, 2, 5, 2)
        hpaned.add1(self.makeWidgets_sidebar())
        hpaned.add2(self.makeWidgets_viewer())
        hpaned.set_position(165)

        # self.layout.attach(self.makeWidgets_settings(), 0, 4, 5, 1)
        self.layout.attach(self.makeWidgets_browser(LIST_GLOSS[0]), 0, 5, 5, 2)


    def makeWidgets_toolbar(self):
        toolbar = Gtk.Toolbar()
        #
        ## Button Back Button
        self.history = Gtk.Menu()
        self.bm_backward = Gtk.MenuToolButton.new_from_stock(Gtk.STOCK_GO_BACK)
        self.bm_backward.set_menu(self.history)
        toolbar.add(self.bm_backward)
        self.bm_backward.connect("clicked", lambda e: self._back_click())
        self.bm_backward.set_tooltip_markup("Previous Search Word, Secondary Click for History Popup, <u>Alt+←</u>")
        self.bm_backward.set_sensitive(False)
        ##
        ## Button Forward Button
        self.b_forward = Gtk.ToolButton.new_from_stock(Gtk.STOCK_GO_FORWARD)
        toolbar.add(self.b_forward)
        self.b_forward.connect("clicked", lambda e: self._forward_click())
        self.b_forward.set_tooltip_markup("Next Search Word, Secondary Click for History Popup, <u>Alt+→</u>")
        self.b_forward.set_sensitive(False)
        ##
        #
        toolbar.add(Gtk.SeparatorToolItem())
        #
        ## Open Gloss
        self.b_open = Gtk.ToolButton.new_from_stock(Gtk.STOCK_OPEN)
        toolbar.add(self.b_open)
        self.b_open.set_tooltip_markup("Clean the Viewer and history, <u>Ctrl+l</u>")
        ##
        ## Properties
        self.b_properties = Gtk.ToolButton.new_from_stock(Gtk.STOCK_PROPERTIES)
        toolbar.add(self.b_properties)
        ##
        ## Add Button
        self.b_add = Gtk.ToolButton.new_from_stock(Gtk.STOCK_ADD)
        toolbar.add(self.b_add)
        self.b_add.connect("clicked", lambda w: self.add_to_gloss())
        self.b_add.set_tooltip_markup("Add new word to glossary, <u>Ctrl+i</u>")
        ##
        #
        toolbar.add(Gtk.SeparatorToolItem())
        #
        ## Auto Transliterate Button
        self.t_trans = Gtk.ToggleToolButton.new_from_stock(Gtk.STOCK_CONVERT)
        toolbar.add(self.t_trans)
        self.t_trans.set_active(True)
        ##
        ## Spell-check Toggle Button
        self.t_spell = Gtk.ToggleToolButton.new_from_stock(Gtk.STOCK_SPELL_CHECK)
        toolbar.add(self.t_spell)
        self.t_spell.set_active(True)
        ##
        ## Smart Copy Toggle Button
        self.t_copy = Gtk.ToggleToolButton.new_from_stock(Gtk.STOCK_COPY)
        toolbar.add(self.t_copy)
        self.t_copy.set_active(True)
        ##
        ## Search Toggle Button
        self.t_search = Gtk.ToggleToolButton.new_from_stock(Gtk.STOCK_DIALOG_INFO)
        self.t_search.set_active(False)
        toolbar.add(self.t_search)
        ##
        #
        toolbar.add(Gtk.SeparatorToolItem())
        #
        ##  Preference
        self.b_preference = Gtk.ToolButton.new_from_stock(Gtk.STOCK_PREFERENCES)
        toolbar.add(self.b_preference)
        self.b_preference.set_tooltip_markup("Change Stuffs, Fonts, default gloss")
        ##
        ## About
        self.b_about = Gtk.ToolButton.new_from_stock(Gtk.STOCK_ABOUT)
        self.b_about.connect("clicked", self._about_dialog)
        toolbar.add(self.b_about)
        self.b_about.set_tooltip_markup("More About Anubad")

        return toolbar


    def _back_click(self):
        print("back clicked")
        self.b_forward.set_sensitive(True)


    def _forward_click(self):
        print("forward clicked")


    def _about_dialog(self, widget):
        aboutdialog = Gtk.AboutDialog(parent=self)
        aboutdialog.set_default_size(200, 300)
        aboutdialog.set_logo_icon_name(Gtk.STOCK_ABOUT)
        aboutdialog.set_program_name(PKG_NAME)
        aboutdialog.set_comments("\nTranslation Glossary\n")
        aboutdialog.set_website("http://github.com/foss-np/anubad/")
        aboutdialog.set_website_label("Some Label")
        aboutdialog.set_authors(open(fullpath + '../AUTHORS').read().splitlines())
        aboutdialog.set_license(open(fullpath + '../LICENSE').read())
        aboutdialog.run()
        aboutdialog.destroy()


    def makeWidgets_searchbar(self):
        layout = Gtk.HBox()

        label = Gtk.Label()
        label.set_markup("<b>Query</b>")
        layout.pack_start(label, expand=False, fill=False, padding=60)

        tool_tip = "<b>Search:</b>\n\t- Normal,\t⌨ [<i>Enter</i>]\n\t- Show All,\t⌨ [<i>Shift + Enter</i>]\nUse Toolbar Toggler to Switch"

        self.search_entry = Gtk.SearchEntry()
        layout.pack_start(self.search_entry, expand=True, fill=True, padding=2)
        self.search_entry.connect('key_release_event', self.search_entry_binds)
        self.search_entry.set_tooltip_markup(tool_tip)

        # accelerators
        accel_search = Gtk.AccelGroup()
        self.add_accel_group(accel_search)
        self.search_entry.add_accelerator("grab_focus", accel_search, ord('f'), Gdk.ModifierType.CONTROL_MASK, 0)

        ## Button
        self.b_search = Gtk.Button(label="Search")
        layout.pack_start(self.b_search, expand=False, fill=False, padding=1)
        self.b_search.connect('clicked', lambda w: self.searchbar_binds(w, None))
        self.b_search.set_tooltip_markup(tool_tip)

        return layout


    def search_entry_binds(self, widget, event):
        # print(event.keyval)
        query = self.search_entry.get_text().strip().lower()
        if event is None:
            self.searchWord(query)
        elif Gdk.ModifierType.CONTROL_MASK & event.state:
            if event.keyval == ord('c'):
                self.search_entry.set_text("")
        elif Gdk.ModifierType.SHIFT_MASK & event.state:
            if event.keyval == 65293: # <enter> return
                state = self.t_search.get_active()
                self.t_search.set_active(not state)
                self.searchWord(query)
                self.t_search.set_active(state)
        elif event.keyval == 65293: # <enter> return
            self.searchWord(query)


    def makeWidgets_sidebar(self):
        layout = Gtk.VBox()

        scroll = Gtk.ScrolledWindow()
        layout.pack_start(scroll, True, True, 0)
        scroll.set_vexpand(False)

        ## TreeView
        self.suggestions = Gtk.ListStore(int, str)
        self.treeview = Gtk.TreeView(model=self.suggestions)
        scroll.add(self.treeview)
        renderer_text = Gtk.CellRendererText()
        self.treeview.append_column(Gtk.TreeViewColumn("#", renderer_text, text=0))
        self.treeview.append_column(Gtk.TreeViewColumn("Suggestions", renderer_text, text=1))
        select = self.treeview.get_selection()
        select.connect("changed", self.on_sidebar_selection)

        ## Filter
        self.cb_filter = Gtk.ComboBoxText()
        layout.pack_start(self.cb_filter, False, False, 0)
        self.cb_filter.append_text("All")
        self.cb_filter.set_active(0)
        # self.cb_filter.connect("changed", category_changed)
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
        self.CLIP_CYCLE = utils.circle(clip_out)
        self._circular_search(+1)


    def makeWidgets_viewer(self):
        global clipboard
        Vi.clipboard = clipboard
        self.viewer = Vi.Viewer(self)
        # self.viewer.connect('key_press_event', self.viewer_binds)
        # self.viewer.textview.override_font(Pango.font_description_from_string('DejaVu Sans Mono 12'))
        self.viewer.textview.modify_font(Pango.font_description_from_string(def_FONT))
        self.viewer.textview.connect('key_press_event', self.viewer_binds)
        return self.viewer


    def viewer_binds(self, widget, event):
        # print(event.keyval)
        # TODO: move it to main

        if event.state & Gdk.ModifierType.CONTROL_MASK or \
           event.state & Gdk.ModifierType.MOD1_MASK or \
           event.state & Gdk.ModifierType.SHIFT_MASK:
            return

        if event.keyval in utils.key_code.values():
            return

        pos = self.search_entry.get_position()
        # print(type(pos), pos)
        self.search_entry.insert_text(chr(event.keyval), pos)
        self.search_entry.grab_focus()
        self.search_entry.select_region(0, 0)
        self.search_entry.set_position(pos + 1)
        # print(dir(self.search_entry))
        self.search_entry_binds(widget, event)


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
                    if word != item[1] and not self.t_search.get_active(): continue
                    self.search_history.append(word)
                    self.history.append(Gtk.MenuItem(label=word))
                    clip_out += self.viewer.parse(tab, obj, row[1:])
                    self.CURRENT_VIEW = found - 1
                    self.VIEWED_ITEMS.add(self.CURRENT_VIEW)
                    foundFlag = True
            if foundFlag is False:
                self.viewer.not_found(word)

        if len(clip_out) == 0:
            self.viewer.jump_to_end()
            return


        if len(self.search_history) > 1:
            self.bm_backward.set_sensitive(True)

        self.search_entry.grab_focus()
        self.CLIP_CYCLE = utils.circle(clip_out)


        if self.t_copy.get_active():
            self._circular_search(+1)


    def open_dir(self):
        print("pid:", Popen(["nemo", self.GLOSS]).pid)


    def open_term(self):
        print("pid:", Popen([TERMINAL, "--working-directory=%s"%self.GLOSS]).pid)


    def reload(self, gloss):
        query = self.search_entry.get_text().strip().lower()
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
            self.search_entry.grab_focus()
            return

        global clipboard
        utils.diff = d
        text = next(self.CLIP_CYCLE)
        self.viewer.mark_found(text)
        if self.t_copy.get_active():
            clipboard.set_text(text, -1)


    def _circular_tab_switch(self, d):
        c = self.notebook.get_current_page()
        t = self.notebook.get_n_pages()
        n = c + d
        if n >= t: n = 0
        elif n < 0: n = t - 1
        self.notebook.set_current_page(n)


    def add_to_gloss(self, query=""):
        _l2 = self.lets_add.strip() if self.lets_add else ""
        global clipboard
        Ad.clipboard = clipboard
        Ad.Add.def_FONT_obj = Pango.font_description_from_string(def_FONT)
        add = Ad.Add(self, l1=query, l2=_l2)

        # TODO: connection
        add.connect('delete-event', self._add_to_gloss_reflect)


    def _add_to_gloss_reflect(self, widget, event):
        print("hello i'm back")


    def key_binds(self, widget, event):
        # print(event.keyval)
        if event.keyval == 65307: Gtk.main_quit() # Esc
        elif event.keyval == 65481: self.reload(LIST_GLOSS[0]) # F12
        elif event.keyval == 65480: self.reload(LIST_GLOSS[1]) # F11
        elif event.keyval == 65479: self.reload(LIST_GLOSS[2]) # F10
        elif event.keyval == 65474: self.reload_gloss() # F5

        global clipboard
        query = self.search_entry.get_text().strip().lower()
        if Gdk.ModifierType.CONTROL_MASK & event.state:
            if event.keyval == ord('i'): self.add_to_gloss(query)
            elif event.keyval == ord('1'): dict_grep(query, self.viewer, False)
            elif event.keyval == ord('2'): web_search(query, self.viewer)
            elif event.keyval == ord('3'): dict_grep(query, self.viewer)
            elif event.keyval == ord('o'): self.open_dir()
            elif event.keyval == ord('t'): self.open_term()
            elif event.keyval == ord('l'): self.viewer.textbuffer.set_text("")
            elif event.keyval == ord('r'): self._circular_search(-1)
            elif event.keyval == ord('s'): self._circular_search(+1)
            elif event.keyval == 65365: self._circular_tab_switch(-1) # pg-down
            elif event.keyval == 65366: self._circular_tab_switch(+1) # pg-up
            elif event.keyval == ord('g'): # grab clipboard
                global clipboard
                clip = clipboard.wait_for_text()
                if clip is None: return
                query = clip.strip().lower()
                self.search_entry.set_text(clip)
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


def root_binds(widget, event):
    # print(event.keyval)
    if event.keyval == 65307:
        Gtk.main_quit()


def main():
    global clipboard
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

    global root
    root = GUI()
    root.connect('delete-event', Gtk.main_quit)

    # gloss trick
    # for obj in self.TAB_LST:
    #     self.TAB_LST.clear()

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
