#!/usr/bin/env python

PKG_NAME = "anubad - अनुवाद"

import os, sys

filepath = os.path.abspath(__file__)
fullpath = os.path.dirname(filepath) + '/'

exec(open(fullpath + "gsettings.conf").read())
exec(open(fullpath + "mysettings.conf").read())

PATH_GLOSS = fullpath + PATH_GLOSS

fp_dev_null = open(os.devnull, 'w')
fp3 = fp_dev_null

if PATH_MYLIB and os.path.isdir(PATH_MYLIB):
    sys.path.append(PATH_MYLIB)
    from debugly import *
    from pprint import pprint
else:
    sys.stdout = fp_dev_null

# func = lambda f, *arg, *karg: f(arg, karg)

from gi.repository import Gtk, Gdk, Pango
from subprocess import Popen
from itertools import count

from utils import treeview_signal_safe_toggler
import preferences as Pre
import browser as BL
import viewer as Vi
import add as Ad
import utils

#   ____ _   _ ___
#  / ___| | | |_ _|
# | |  _| | | || |
# | |_| | |_| || |
#  \____|\___/|___|
#
class GUI(Gtk.Window):
    clip_CYCLE = None
    notebook_OBJS = []

    def __init__(self, parent=None):
        Gtk.Window.__init__(self, title=PKG_NAME)
        self.set_default_size(600, 500)
        self.parent = parent
        self.track_FONT = set()

        self.items_FOUND = []
        self.items_VIEWED = set() # TODO: Fix it
        self.views_CURRENT = []

        self.hist_LIST = []
        self.hist_CURSOR = 0


        self.ignore_keys = [ v for k, v in utils.key_codes.items() if v != utils.key_codes["RETURN"]]

        self.makeWidgets()
        self.connect('key_press_event', self.key_binds)
        self.search_entry.grab_focus()
        self.show_all()
        # NOTE: GTK BUG, notebook page switch only after its visible
        self.notebook.set_current_page(self.notebook.MAIN_TAB)


    def makeWidgets(self):
        self.layout = Gtk.Grid()
        self.add(self.layout)

        self.toolbar = self.makeWidgets_toolbar()
        self.layout.attach(self.toolbar, left=0, top=0, width=5, height=1)
        self.layout.attach(self.makeWidgets_searchbar(), 0, 1, 5, 1)

        hpaned = Gtk.Paned()
        self.layout.attach(hpaned, 0, 2, 5, 2)
        hpaned.add1(self.makeWidgets_sidebar())
        hpaned.add2(self.makeWidgets_viewer())
        hpaned.set_position(165)

        self.notebook = self.makeWidgets_browser(LIST_GLOSS[0])
        self.layout.attach(self.notebook, 0, 5, 5, 2)


    def makeWidgets_toolbar(self):
        bar = Gtk.Toolbar()
        #
        ## Button Back Button
        bar.bm_Backward = Gtk.MenuToolButton(icon_name=Gtk.STOCK_GO_BACK)
        bar.add(bar.bm_Backward)
        bar.bm_Backward.connect("clicked", lambda e: self._jump_history(-1))
        bar.bm_Backward.set_tooltip_markup("Previous Search Word, Secondary Click for History Popup, <u>Alt+←</u>")
        bar.bm_Backward.set_sensitive(False)
        ### History
        # TODO: find the widget flag
        self.hist_menu_toggle_state = False
        self.history_menu = Gtk.Menu() # NOTE: DUMMY MENU For Menu activation
        bar.bm_Backward.set_menu(self.history_menu)
        bar.bm_Backward.connect("show-menu", lambda e: self._show_history(e))
        ##
        ## Button Forward Button
        bar.b_Forward = Gtk.ToolButton(icon_name=Gtk.STOCK_GO_FORWARD)
        bar.add(bar.b_Forward)
        bar.b_Forward.connect("clicked", lambda e: self._jump_history(+1))
        bar.b_Forward.set_tooltip_markup("Next Search Word, Secondary Click for History Popup, <u>Alt+→</u>")
        bar.b_Forward.set_sensitive(False)
        ##
        #
        bar.add(Gtk.SeparatorToolItem())
        #
        ## Open Gloss
        bar.b_Open = Gtk.ToolButton(icon_name=Gtk.STOCK_OPEN)
        bar.add(bar.b_Open)
        bar.b_Open.connect("clicked", lambda w: self._open_dir())
        bar.b_Open.set_tooltip_markup("Load New Glossary")
        ##
        ## Add Button
        bar.b_Add = Gtk.ToolButton(icon_name=Gtk.STOCK_ADD)
        bar.add(bar.b_Add)
        bar.b_Add.connect("clicked", lambda w: self.add_to_gloss())
        bar.b_Add.set_tooltip_markup("Add new word to Glossary, <u>Ctrl+i</u>")
        ##
        ## Refresh
        bar.b_Refresh = Gtk.ToolButton(icon_name=Gtk.STOCK_REFRESH)
        bar.add(bar.b_Refresh)
        bar.b_Refresh.connect("clicked", lambda w: self._reload_gloss())
        bar.b_Refresh.set_tooltip_markup("Refresh Reload Current Glossary, <u>Ctrl+F5</u>")
        ##
        #
        bar.add(Gtk.SeparatorToolItem())
        #
        ## Smart Copy Toggle Button
        bar.t_Copy = Gtk.ToggleToolButton(icon_name=Gtk.STOCK_COPY)
        bar.add(bar.t_Copy)
        bar.t_Copy.set_active(True)
        ##
        ## Search Toggle Button
        bar.t_Search = Gtk.ToggleToolButton(icon_name=Gtk.STOCK_DIALOG_INFO)
        bar.t_Search.set_active(False)
        bar.add(bar.t_Search)
        ##
        #
        bar.add(Gtk.SeparatorToolItem())
        #
        ##  Preference
        bar.b_Preference = Gtk.ToolButton(icon_name=Gtk.STOCK_PREFERENCES)
        bar.add(bar.b_Preference)
        bar.b_Preference.connect("clicked", lambda w: self.preference())
        bar.b_Preference.set_tooltip_markup("Change Stuffs, Fonts, default gloss")

        ##
        ## About
        bar.b_About = Gtk.ToolButton(icon_name=Gtk.STOCK_ABOUT)
        bar.b_About.connect("clicked", self._about_dialog)
        bar.add(bar.b_About)
        bar.b_About.set_tooltip_markup("More About Anubad")
        return bar


    def _jump_history(self, diff):
        pos = self.hist_CURSOR + diff

        if 0 > pos: return
        elif len(self.hist_LIST) <= pos:
            self.toolbar.b_Forward.set_sensitive(False)
            return

        if diff == -1: self.toolbar.b_Forward.set_sensitive(True)

        self.hist_CURSOR = pos

        self.items_FOUND.clear()
        self.views_CURRENT.clear()
        query, self.items_FOUND, views = self.hist_LIST[pos]
        self._view_items(views)
        self.search_entry.set_text(query)


    def _show_history(self, widget):
        # print(widget.get_state_flags())
        # TODO: fix state with widget attrib
        state = self.hist_menu_toggle_state
        self.hist_menu_toggle_state = not state
        if state: return

        del self.history_menu
        self.history_menu = Gtk.Menu()
        widget.set_menu(self.history_menu)

        for i, (query, items, views) in enumerate(reversed(self.hist_LIST), 1):
            rmi = Gtk.RadioMenuItem(label=query)
            rmi.show()
            if len(self.hist_LIST) - i == self.hist_CURSOR:
                rmi.set_active(True)
            self.history_menu.append(rmi)

        self.history_menu.show_all()


    def _about_dialog(self, widget):
        aboutdialog = Gtk.AboutDialog(parent=self)
        # aboutdialog.set_default_size(200, 800) # BUG: Not WORKING
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
        ### Font stuff
        self.search_entry.modify_font(FONT_obj)
        self.track_FONT.add(self.search_entry)

        # accelerators
        accel_search = Gtk.AccelGroup()
        self.add_accel_group(accel_search)
        self.search_entry.add_accelerator("grab_focus", accel_search, ord('f'), Gdk.ModifierType.CONTROL_MASK, 0)

        ## Button
        self.b_search = Gtk.Button(label="Search")
        layout.pack_start(self.b_search, expand=False, fill=False, padding=1)
        self.b_search.connect('clicked', lambda w: self.search_entry_binds(w, None))
        self.b_search.set_tooltip_markup(tool_tip)

        return layout


    def search_entry_binds(self, widget, event):
        # print(event.keyval)
        # TODO: make the wrapper around .get_text()
        raw_query = self.search_entry.get_text()
        if 'r:' == raw_query[:2]: query = raw_query[2:]
        else: query = raw_query.strip().lower()

        if event is None: self.searchWord(query)
        elif Gdk.ModifierType.CONTROL_MASK & event.state:
            if event.keyval == ord('c'): self.search_entry.set_text("")
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

        ## TreeView #TODO put sensible name and hierarchy
        self.suggestions = Gtk.ListStore(int, str)
        self.treeview = Gtk.TreeView(model=self.suggestions)
        scroll.add(self.treeview)
        # self.treeview.set_rubber_banding(True)
        self.treeview.connect("row-activated", self.sidebar_row_double_click)
        ### Font stuff
        self.treeview.modify_font(FONT_obj)
        self.track_FONT.add(self.treeview)

        select = self.treeview.get_selection()
        # TODO: multiple selection FIXME
        # select.set_mode(Gtk.SelectionMode.MULTIPLE)
        self.select_signal = select.connect("changed", self.sidebar_on_row_select)

        renderer_text = Gtk.CellRendererText()
        self.treeview.append_column(Gtk.TreeViewColumn("#", renderer_text, text=0))
        self.treeview.append_column(Gtk.TreeViewColumn("Suggestions", renderer_text, text=1))

        ## Filter
        self.cb_filter = Gtk.ComboBoxText()
        layout.pack_start(self.cb_filter, False, False, 0)
        self.cb_filter.append_text("All")
        self.cb_filter.set_active(0)
        # self.cb_filter.connect("changed", category_changed)
        return layout


    def sidebar_bind(self, widget, event):
        print("TODO: pass the signal")
        pass


    def sidebar_on_row_select(self, selection):
        if not self.items_FOUND: return

        model, treeiter = selection.get_selected()
        if treeiter is None: return
        i = model[treeiter][0] - 1
        self.views_CURRENT.clear()
        self.views_CURRENT.append(i)

        p = i not in self.items_VIEWED
        self.items_VIEWED.add(i)

        tab, obj, *row = self.items_FOUND[i]
        clip_out = self.viewer.parse(tab, obj, row, _print=p)
        GUI.clip_CYCLE = utils.circle(clip_out)
        self._circular_search(+1)


    def sidebar_row_double_click(self, widget, treepath, treeviewcol):
        # TODO: fix it with the widget using CURRENT_VIEW IS NOT GOOD
        if len(self.views_CURRENT) == 0:
            print("Need to fix")
            return

        tab, obj, n, *row = self.items_FOUND[self.views_CURRENT[0]]
        self.notebook.set_current_page(tab)
        obj.treeview.set_cursor(n-1)


    def makeWidgets_viewer(self):
        global clipboard
        Vi.clipboard = clipboard
        self.viewer = Vi.Viewer(self)
        self.viewer.textview.modify_font(FONT_obj)
        self.track_FONT.add(self.viewer.textview)

        # new_clean = lambda: self.viewer.clean()
        # FIX-ME: make it in lambda function, decorator
        old_clean = self.viewer.clean
        def new_clean():
            old_clean()
            self.views_CURRENT.clear()
            self.items_VIEWED.clear()
            # NOTE: vvv is for sugession
            selection = self.treeview.get_selection()
            selection.unselect_all()
        self.viewer.clean = new_clean

        return self.viewer


    def makeWidgets_browser(self, gloss):
        GLOSS = PATH_GLOSS + gloss
        print("loading:", gloss, file=sys.stderr)
        notebook = Gtk.Notebook()
        notebook.GLOSS = GLOSS
        tab = 0
        for file_name in os.listdir(GLOSS):
            if not file_name[-4:] in FILE_TYPES: continue
            if "main.tra" in file_name: notebook.MAIN_TAB = tab
            obj = BL.BrowseList(self.parent, GLOSS + file_name)
            obj.treeview.connect("row-activated", self.browser_row_double_click)
            obj.treeview.modify_font(FONT_obj)
            self.track_FONT.add(obj.treeview)
            notebook.append_page(obj, Gtk.Label(label=file_name[:-4]))
            tab += 1
        GUI.notebook_OBJS.append(notebook)
        return notebook


    def browser_row_double_click(self, widget, treepath, treeviewcol):
        selection = widget.get_selection()
        model, treeiter = selection.get_selected()

        if treeiter is None: return
        tab = self.notebook.get_current_page()
        obj = self.notebook.get_nth_page(tab)
        row = list(model[treeiter])
        self.viewer.parse(tab, obj, row)
        self.viewer.jump_to_end()
        return


    def searchWord(self, query):
        search_space = []
        for obj in self.notebook_OBJS:
            for i in count():
                widget = obj.get_nth_page(i)
                if widget is None: break
                search_space.append((i, widget))

        if not query: return

        items_FOUND = []
        views_CURRENT = []
        found = 0

        for word in set(query.split()):
            foundFlag = False
            # TODO: make it simpler
            # MAYBE: put the tree search in browserlst itself
            for tab, obj in search_space:
                for item in obj.treebuffer:
                    if word not in item[1]: continue
                    found += 1
                    row = [tab, obj] + list(item)
                    ## remove duplicate longest str match
                    if row not in items_FOUND: items_FOUND.append(row)
                    ## exact match filter
                    if word != item[1] and not self.toolbar.t_Search.get_active(): continue
                    views_CURRENT.append(found - 1)
                    foundFlag = True
            if foundFlag is False:
                self.viewer.not_found(word)
                dict_grep2(query.lower(), self.viewer, False)

        if len(items_FOUND) == 0:
            self.viewer.jump_to_end()
            return

        del self.items_FOUND
        self.items_FOUND = items_FOUND
        self._view_items(views_CURRENT)

        self.hist_LIST.append((query, items_FOUND[:], views_CURRENT[:]))
        self.hist_CURSOR = len(self.hist_LIST) - 1
        self.toolbar.bm_Backward.set_sensitive(True)
        self.toolbar.b_Forward.set_sensitive(False)


    @treeview_signal_safe_toggler
    def _view_items(self, views_CURRENT):
        self.suggestions.clear()
        self.items_VIEWED.clear()

        for i, item in enumerate(self.items_FOUND, 1):
            self.suggestions.append([i, item[3]])

        if len(views_CURRENT) == 0:
            return

        clip_out = []
        for view in views_CURRENT:
            # TODO fix view here
            self.treeview.set_cursor(view)
            tab, obj, *row = self.items_FOUND[view]
            clip_out += self.viewer.parse(tab, obj, row)
            self.items_VIEWED.add(view)

        del self.views_CURRENT
        self.views_CURRENT = views_CURRENT

        GUI.clip_CYCLE = utils.circle(clip_out)
        self._circular_search(+1)

        self.search_entry.grab_focus()


    def _open_dir(self):
        print("pid:", Popen(["nemo", self.notebook.GLOSS]).pid)


    def _open_term(self):
        print("pid:", Popen([TERMINAL, "--working-directory=%s"%self.notebook.GLOSS]).pid)


    def _open_src(self):
        if self.views_CURRENT is None: return
        t, obj, _id, *etc = self.items_FOUND[self.views_CURRENT[0]]
        self.notebook.get_nth_page(t).open_src(_id)
        # TODO: connection
        # process.connect('delete-event', self.open_src)


    def reload(self, gloss):
        GLOSS = PATH_GLOSS + gloss
        if self.notebook.GLOSS == GLOSS: return

        self.layout.remove(self.notebook)
        for obj in GUI.notebook_OBJS:
            if obj.GLOSS == GLOSS:
                self.notebook = obj
                break
        else:
            self.notebook = self.makeWidgets_browser(gloss)

        self.layout.attach(self.notebook, 0, 5, 5, 2)
        self.show_all()
        self.notebook.set_current_page(self.notebook.MAIN_TAB)


    def _reload_gloss(self):
        current_tab = self.notebook.get_current_page()
        obj = self.notebook.get_nth_page(current_tab)
        print("reload:", obj.SRC[-30:], file=sys.stderr)
        obj.treebuffer.clear()
        obj.fill_tree(obj.SRC)


    def _circular_search(self, d):
        if not GUI.clip_CYCLE:
            self.search_entry.grab_focus()
            return

        global clipboard
        utils.diff = d
        text = next(GUI.clip_CYCLE)
        self.viewer.mark_found(text)
        if self.toolbar.t_Copy.get_active():
            clipboard.set_text(text, -1)


    def _circular_tab_switch(self, d):
        c = self.notebook.get_current_page()
        t = self.notebook.get_n_pages()
        n = c + d
        if n >= t: n = 0
        elif n < 0: n = t - 1
        self.notebook.set_current_page(n)


    def add_to_gloss(self, query=""):
        global clipboard
        Ad.clipboard = clipboard
        add = Ad.Add(self, l1=query, l2="")
        for obj in add.track_FONT:
            obj.modify_font(FONT_obj)
        # TODO: connection
        add.connect('delete-event', self._add_to_gloss_reflect)


    def _add_to_gloss_reflect(self, widget, event):
        print("hello i'm back")


    def preference(self, query=""):
        Pre.def_FONT = def_FONT
        s = Pre.Settings(self)


    def key_binds(self, widget, event):
        # print(e.keyval)
        keyval, state = event.keyval, event.state
        query = self.search_entry.get_text().strip().lower()
        if   keyval == 65307: Gtk.main_quit() # Esc
        elif keyval == 65481: self.reload(LIST_GLOSS[0]) # F12
        elif keyval == 65480: self.reload(LIST_GLOSS[1]) # F11
        elif keyval == 65479: self.reload(LIST_GLOSS[2]) # F10
        elif keyval == 65476: xcowsay(query) # F7
        elif keyval == 65474: self._reload_gloss() # F5
        elif keyval == 65362: self.sidebar_bind(widget, event)# UP-Arrow
        elif keyval == 65364: self.sidebar_bind(widget, event)# DOWN-Arrow
        elif Gdk.ModifierType.CONTROL_MASK & state:
            if   keyval == ord('1'): dict_grep2(query, self.viewer, False)
            elif keyval == ord('2'): dict_grep(query, self.viewer, False)
            elif keyval == ord('3'): web_search(query, self.viewer)
            elif keyval == ord('4'): dict_grep(query, self.viewer)
            elif keyval == ord('e'): self._open_src()
            elif keyval == ord('i'): self.add_to_gloss(query)
            elif keyval == ord('l'): self.viewer.clean()
            elif keyval == ord('o'): self._open_dir()
            elif keyval == ord('r'): self._circular_search(-1)
            elif keyval == ord('s'): self._circular_search(+1)
            elif keyval == ord('t'): self._open_term()
            elif keyval == 65365: self._circular_tab_switch(-1) # pg-down
            elif keyval == 65366: self._circular_tab_switch(+1) # pg-up
            elif keyval == ord('g'): # grab clipboard
                clip = clipboard.wait_for_text()
                if clip is None: return
                query = clip.strip().lower()
                self.search_entry.set_text(clip)
                self.searchWord(query)
            return
        elif Gdk.ModifierType.MOD1_MASK & state:
            if ord('1') <= keyval <= ord('9'):
                t = keyval - ord('1')
                # NOTE: range check not needed
                self.notebook.set_current_page(t)
            elif keyval == ord('0'): self.notebook.set_current_page(self.MAIN_TAB)
            elif keyval == 65361: self._jump_history(-1) # LEFT_ARROW
            elif keyval == 65363: self._jump_history(+1) # RIGHT_ARROW
            return
        elif Gdk.ModifierType.SHIFT_MASK & event.state:
            if   keyval == 65365: pass # pg-down
            elif keyval == 65366: pass # pg-up
            return

        if self.search_entry.is_focus(): return

        if event.keyval in self.ignore_keys: return

        self.search_entry.grab_focus()
        pos = self.search_entry.get_position()
        self.search_entry.set_position(pos + 1)
        self.search_entry_binds(widget, event)


def load_settings():
    global FONT_obj
    FONT_obj =  Pango.font_description_from_string(def_FONT)
    BL.fp3 = fp3


def root_binds(widget, event):
    # print(event.keyval)
    if event.keyval == 65307:
        Gtk.main_quit()


def main():
    load_settings()

    global clipboard
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

    global root
    root = GUI()
    root.connect('delete-event', Gtk.main_quit)

    return root


if __name__ == '__main__':
    main().connect('key_press_event', root_binds)
    global PATH_PLUGINS
    PATH_PLUGINS = fullpath + PATH_PLUGINS
    if PATH_PLUGINS and os.path.isdir(PATH_PLUGINS):
        for file_name in os.listdir(PATH_PLUGINS):
            if file_name[-3] not in ".py": continue
            print("plugin:", file_name, file=sys.stderr)
            exec(open(PATH_PLUGINS + file_name).read())
    Gtk.main()
