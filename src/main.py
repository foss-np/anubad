#!/usr/bin/env python

PKG_NAME = "anubad - अनुवाद"

import os, sys

filepath = os.path.abspath(__file__)
fullpath = os.path.dirname(filepath) + '/'

exec(open(fullpath + "gsettings.conf", encoding="UTF-8").read())
exec(open(fullpath + "mysettings.conf", encoding="UTF-8").read())

PATH_GLOSS = fullpath + PATH_GLOSS

fp_dev_null = open(os.devnull, 'w')
fp3 = fp_dev_null

from gi.repository import Gtk, Gdk, Pango
from collections import OrderedDict
from subprocess import Popen
from itertools import count

from utils import treeview_signal_safe_toggler
import preferences as Pre
import browser as BL
import viewer as Vi
import add as Ad
import utils

if PATH_MYLIB and os.path.isdir(PATH_MYLIB):
    sys.path.append(PATH_MYLIB)
    from debugly import *
    from pprint import pprint
else:
    sys.stdout = fp_dev_null
    debug = lambda f, *arg, **karg: f(arg, karg)

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

        self.view_CURRENT = set()
        self.view_LAST = None

        self.hist_LIST = []
        self.hist_CURSOR = 0


        self.ignore_keys = [ v for k, v in utils.key_codes.items() if v != utils.key_codes["RETURN"]]

        self.makeWidgets()
        self.connect('key_press_event', self.key_binds)
        self.connect('delete-event', Gtk.main_quit)
        self.connect('focus-in-event', lambda *e: self.search_entry.grab_focus())

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
        bar.bm_Backward.set_tooltip_markup("Previous, <u>Alt+←</u>")
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
        bar.b_Forward.set_tooltip_markup("Next, <u>Alt+→</u>")
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
        #
        bar.add(Gtk.SeparatorToolItem())
        #
        ## Smart Copy Toggle Button
        bar.t_Copy = Gtk.ToggleToolButton(icon_name=Gtk.STOCK_COPY)
        bar.add(bar.t_Copy)
        bar.t_Copy.set_active(True)
        ##
        ## Search Show Toggle Button
        bar.t_ShowAll = Gtk.ToggleToolButton(icon_name=Gtk.STOCK_DIALOG_INFO)
        bar.t_ShowAll.set_active(False)
        bar.add(bar.t_ShowAll)
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
        self.search_entry.set_max_length(80)
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
        # FIXME this cheat signal not forwarded
        if   event is None: self.search_and_reflect()
        elif Gdk.ModifierType.CONTROL_MASK & event.state:
            if event.keyval == ord('c'): self.search_entry.set_text("")
        elif Gdk.ModifierType.SHIFT_MASK & event.state:
            if event.keyval == 65293: # <enter> return
                print("shift enter")
                state = self.toolbar.t_ShowAll.get_active()
                self.toolbar.t_ShowAll.set_active(not state)
                self.search_and_reflect()
                self.toolbar.t_ShowAll.set_active(not state)
        elif event.keyval == 65293: self.search_and_reflect() # <enter> return


    def makeWidgets_sidebar(self):
        layout = Gtk.VBox()

        scroll = Gtk.ScrolledWindow()
        layout.pack_start(scroll, True, True, 0)
        scroll.set_vexpand(False)

        ## TreeView #TODO put sensible name and hierarchy
        self.suggestions = Gtk.ListStore(int, int, int, int, str)
        self.treeview = Gtk.TreeView(model=self.suggestions)
        scroll.add(self.treeview)
        # self.treeview.set_rubber_banding(True)
        self.treeview.connect("row-activated", self.sidebar_row_double_click)
        ### Font stuff
        self.treeview.modify_font(FONT_obj)
        self.track_FONT.add(self.treeview)

        select = self.treeview.get_selection()
        # TODO: multiple selection FIXME
        select.set_mode(Gtk.SelectionMode.MULTIPLE)
        self.select_signal = select.connect("changed", self.sidebar_on_row_select)

        renderer_text = Gtk.CellRendererText()
        # for i, (label, vis) in enumerate(zip("#ntiw", "10001")):
        #     col = Gtk.TreeViewColumn(label, renderer_text, text=i)
        #     col.set_visible(True)#True if vis is '1' else False)
        #     self.treeview.append_column(col)

        self.treeview.set_headers_visible(False)
        self.treeview.append_column(Gtk.TreeViewColumn('#', renderer_text, text=0))
        self.treeview.append_column(Gtk.TreeViewColumn('w', renderer_text, text=4))

        ## Filter
        self.cb_filter = Gtk.ComboBoxText()
        layout.pack_start(self.cb_filter, False, False, 0)
        self.cb_filter.append_text("All")
        self.cb_filter.set_active(0)
        # self.cb_filter.connect("changed", category_changed)
        return layout


    def sidebar_bind(self, widget, event):
        print("TODO: pass the action as well")
        pass


    def sidebar_on_row_select(self, treeselection):
        model, pathlist = treeselection.get_selected_rows()
        clip_out = []
        for path in pathlist:
            c, note, tab, ID, w = self.suggestions[path]
            note_obj = GUI.notebook_OBJS[note]
            browser_obj = note_obj.get_nth_page(tab)
            treerow = browser_obj.treebuffer[ID-1]
            meta = (note, tab, ID)
            view = meta not in self.view_CURRENT
            clip_out += self.viewer.parse(treerow, browser_obj.SRC, print_=view)
            self.view_CURRENT.add(meta)

        if len(clip_out) > 0:
            GUI.clip_CYCLE = utils.circle(clip_out)
            self._circular_search(+1)


    def sidebar_row_double_click(self, widget, treepath, treeviewcol):
        path, column = widget.get_cursor()
        # tab, obj, n, *row = self.items_FOUND[path[0]]
        # self.notebook.set_current_page(tab)
        # obj.treeview.set_cursor(n-1)


    def makeWidgets_viewer(self):
        global clipboard
        Vi.clipboard = clipboard
        self.viewer = Vi.Viewer(self)
        self.viewer.textview.modify_font(FONT_obj)
        self.track_FONT.add(self.viewer.textview)

        old_clean = self.viewer.clean
        # FIX-ME: make it real smart
        def smart_clean():
            old_clean()
            # TODO last clean job after view is fixed
            # if len(self.items_VIEWED) > 1:
            #     self.view_last
            self.view_CURRENT.clear()
            # NOTE: vvv is for sugession
            selection = self.treeview.get_selection()
            selection.unselect_all()
            # model, treeiter = selection.get_selected()
            # if treeiter is None:
            #     print("It clean")
        self.viewer.clean = smart_clean

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


    def search_and_reflect(self):
        raw_query = self.search_entry.get_text()
        if not raw_query: return
        if 'r:' == raw_query[:2]: query = raw_query[2:]
        else: query = raw_query.strip().lower()

        search_SPACE = []
        for i, obj in enumerate(self.notebook_OBJS):
            for c in count():
                widget = obj.get_nth_page(c)
                if widget is None: break
                search_SPACE.append((i, c, widget))

        ## Ordered Dict use for undo/redo history
        query_RESULTS = OrderedDict()
        all_FUZZ = set()
        for word in set(query.split()):
            n, FULL, FUZZ = self.searchWord(word, search_SPACE)
            query_RESULTS[word] = (FULL, n is not 0)
            all_FUZZ = all_FUZZ | FUZZ

        self._view_items(query_RESULTS, all_FUZZ)

        self.hist_LIST.append((query_RESULTS, all_FUZZ))
        self.hist_CURSOR = len(self.hist_LIST) - 1
        self.toolbar.bm_Backward.set_sensitive(True)
        self.toolbar.b_Forward.set_sensitive(False)


    def searchWord(self, word, search_space):
        FULL, FUZZ = [], set()
        c = 0
        for note, tab, obj in search_space:
            for item in obj.treebuffer:
                if word not in item[1]: continue
                c += 1
                row = (note, tab, item)
                if word == item[1]: FULL.append(row)
                else: FUZZ.add(row)
        return c, FULL, FUZZ


    @treeview_signal_safe_toggler
    def _view_items(self, query_RESULTS, all_FUZZ=set()):
        self.suggestions.clear()
        treeselection = self.treeview.get_selection()

        # pprint(query_RESULTS)
        clip_out = []
        c = 0
        for word, (results, found) in query_RESULTS.items():
            if not found:
                self.viewer.not_found(word)
                dict_grep2(word, self.viewer, False)
                continue
            for item in results:
                note, tab, treerow = item
                ID, w, raw = treerow

                note_obj = GUI.notebook_OBJS[note]
                browser_obj = note_obj.get_nth_page(tab)

                meta = (note, tab, ID)
                view = meta not in self.view_CURRENT
                clip_out += self.viewer.parse(treerow, browser_obj.SRC, print_=view)

                self.view_CURRENT.add(meta)
                c += 1
                self.suggestions.append([c, note, tab, ID, w])
                treeselection.select_path(c - 1)

        for item in all_FUZZ:
            note, tab, treerow = item
            ID, w, raw = treerow
            c += 1
            self.suggestions.append([c, note, tab, ID, w])
            if not self.toolbar.t_ShowAll.get_active(): continue

            note_obj = GUI.notebook_OBJS[note]
            browser_obj = note_obj.get_nth_page(tab)

            meta = (note, tab, ID)
            view = meta not in self.view_CURRENT
            clip_out += self.viewer.parse(treerow, browser_obj.SRC, print_=view)
            self.view_CURRENT.append((note, tab, ID))
            treeselection.select_path(c-1)

        if len(self.view_CURRENT) == 0: return
        GUI.clip_CYCLE = utils.circle(clip_out)
        self._circular_search(+1)
        self.search_entry.grab_focus()


    def _open_dir(self):
        print("pid:", Popen(["nemo", self.notebook.GLOSS]).pid)


    def _open_term(self):
        print("pid:", Popen([TERMINAL, "--working-directory=%s"%self.notebook.GLOSS]).pid)


    def _open_src(self):
        if self.items_FOUND:
            t, obj, _id, *etc = self.items_FOUND[self.views_CURRENT[0]]
        else:
            t = self.notebook.get_current_page()
            _id = None

        self.notebook.get_nth_page(t).open_src(_id)
        # TODO: connection
        # process.connect('delete-event', lambda e: print("i'm back"))


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
        obj.reload()


    def _circular_search(self, d):
        if not GUI.clip_CYCLE:
            self.search_entry.grab_focus()
            return

        global clipboard
        utils.diff = d
        text = next(GUI.clip_CYCLE)

        begin = self.viewer.textbuffer.get_start_iter()
        end = self.viewer.textbuffer.get_end_iter()

        self.viewer.textbuffer.remove_tag(self.viewer.tag_found, begin, end)
        position = self.viewer.mark_found(text, begin)
        m = self.viewer.textbuffer.create_mark("tmp", position)
        self.viewer.textview.scroll_mark_onscreen(m)
        self.viewer.textbuffer.delete_mark(m)

        if self.toolbar.t_Copy.get_active():
            clipboard.set_text(text, -1)


    def _circular_tab_switch(self, d):
        c = self.notebook.get_current_page()
        t = self.notebook.get_n_pages()
        n = c + d
        if n >= t: n = 0
        elif n < 0: n = t - 1
        self.notebook.set_current_page(n)
        # obj = self.notebook.get_nth_page(n)
        # obj.grab_focus()


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
            if   keyval == ord('1'): print(dict_grep2(query, self.viewer, False))
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
                # obj = self.notebook.get_nth_page(t)
                # if obj == None: return
                self.notebook.set_current_page(t) # NOTE: range check not needed
                # obj.grab_focus()
            elif keyval == ord('0'): self.notebook.set_current_page(self.MAIN_TAB)
            elif keyval == 65361: self._jump_history(-1) # LEFT_ARROW
            elif keyval == 65363: self._jump_history(+1) # RIGHT_ARROW
            return
        elif Gdk.ModifierType.SHIFT_MASK & event.state:
            # TODO Scroll viewer
            if   keyval == 65365: pass # pg-down
            elif keyval == 65366: pass # pg-up
            return

        if event.keyval in self.ignore_keys: return
        if self.search_entry.is_focus(): return

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

    return root


if __name__ == '__main__':
    main().connect('key_press_event', root_binds)
    PATH_PLUGINS = fullpath + PATH_PLUGINS
    if PATH_PLUGINS and os.path.isdir(PATH_PLUGINS):
        # TODO: load plugins as modules
        sys.path.append(PATH_PLUGINS)
        for file_name in os.listdir(PATH_PLUGINS):
            if file_name[-3:] not in ".py": continue
            print("plugin:", file_name, file=sys.stderr)
            # import file_name[:-3]
            exec(open(PATH_PLUGINS + file_name, encoding="UTF-8").read())
    Gtk.main()
