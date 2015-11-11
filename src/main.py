#!/usr/bin/env python3

import os, sys

__filepath__ = os.path.abspath(__file__)
PWD = os.path.dirname(__filepath__) + '/'

exec(open(PWD + "gsettings.conf", encoding="UTF-8").read())
exec(open(PWD + "mysettings.conf", encoding="UTF-8").read())

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Pango

import importlib
from collections import OrderedDict
from subprocess import Popen
from itertools import count

import core
import preferences as Pre
import sidebar as Side
import browser
import viewer as Vi
import relations
import add as Ad
import utils

fp_dev_null = open(os.devnull, 'w')

DEBUG = 0
if "DEBUG" in os.environ:
    try:
        DEBUG = int(os.environ["DEBUG"])
    except:
        DEBUG = 1

if 'DEBUGLY' in globals() and os.path.isdir(DEBUGLY) and DEBUG:
    sys.path.append(DEBUGLY)
    from debugly import *
else:
    debug = lambda func: func

for i in range(3, 7):
    if DEBUG > 0:
        print("DEBUG: %d fp%d enabled"%(DEBUG, i), file=sys.stderr)
        stream = "sys.stderr"
        DEBUG -= 1
    else:
        stream = "fp_dev_null"
    exec("fp%d = %s"%(i, stream))


def treeview_signal_safe_toggler(func):
    '''Gtk.TreeView() :changed: signal should be disable before new
    selection is added, if connect it will trigger the change.

    '''
    def wrapper(self, *args, **kwargs):
        treeselection = self.sidebar.treeview.get_selection()
        treeselection.disconnect(self.sidebar.select_signal)
        func_return = func(self, *args, **kwargs)
        self.sidebar.select_signal = treeselection.connect("changed", self.sidebar_on_row_changed)
        return func_return
    return wrapper

#   ____ _   _ ___
#  / ___| | | |_ _|
# | |  _| | | || |
# | |_| | |_| || |
#  \____|\___/|___|
#
class GUI(Gtk.Window):
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

    def __init__(self, parent=None):
        Gtk.Window.__init__(self)
        self.parent = parent
        self.track_FONT = set()

        self.clips = []
        self.clips_CYCLE = None

        self.view_CURRENT = set()
        self.mark_CURRENT = (None, None)

        self.hist_LIST = []
        self.hist_CURSOR = 0
        self.copy_BUFFER = ""

        self.engines = {
            'r:': lambda query: self._view_results({ query: core.Glossary.search(query[2:]) }),
            # w: lambda: self._view_results({ query: core.Glossary.search(query[2:]) }),
            # s:
        }

        # accelerators
        self.makeWidgets()
        self.connect('key_release_event', self.key_binds)
        self.connect('delete-event', Gtk.main_quit)
        self.connect('focus-in-event', lambda *e: self.search_entry.grab_focus())
        self.connect('focus-out-event', lambda *e: self._on_focus_out_event())

        self.search_entry.grab_focus()
        self.set_default_size(600, 550)
        self.show_all()


    def turn_off_auto_copy(func):
        def wrapper(self, *args, **kwargs):
            self.toolbar.t_Copy.set_active(False)
            return func(self, *args, **kwargs)
        return wrapper


    def _on_focus_out_event(self):
        if self.toolbar.t_Copy.get_active():
            __class__.clipboard.set_text(self.copy_BUFFER, -1)


    def makeWidgets(self):
        self.layout = Gtk.Grid()
        self.add(self.layout)

        self.toolbar = self.makeWidgets_toolbar()
        self.layout.attach(self.toolbar, left=0, top=0, width=5, height=1)
        self.layout.attach(self.makeWidgets_searchbar(), left=0, top=1, width=5, height=1)

        hpaned = Gtk.Paned()
        self.layout.attach(hpaned, left=0, top=2, width=5, height=2)
        hpaned.add1(self.makeWidgets_sidebar())
        hpaned.add2(self.makeWidgets_viewer())
        hpaned.set_position(165)

        # self.layout.attach(self.makeWidgets_relations(), left=0, top=5, width=5, height=2)


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
        # bar.b_Add.connect("clicked", lambda w: self.add_to_gloss())
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
        bar.t_WordNet = Gtk.ToggleToolButton(icon_name=Gtk.STOCK_DIALOG_INFO)
        bar.t_WordNet.set_active(False)
        bar.t_WordNet.set_tooltip_markup("Dictionary Mode (WordNet)")
        bar.add(bar.t_WordNet)
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
        self._view_results(self.hist_LIST[pos])


    def _show_history(self, widget):
        state = self.hist_menu_toggle_state
        self.hist_menu_toggle_state = not state
        if state: return

        del self.history_menu
        self.history_menu = Gtk.Menu()
        widget.set_menu(self.history_menu)

        for i, query_RESULTS in enumerate(reversed(self.hist_LIST), 1):
            query = ', '.join([ k for k in query_RESULTS.keys() ])
            rmi = Gtk.RadioMenuItem(label=query)
            rmi.show()
            if len(self.hist_LIST) - i == self.hist_CURSOR:
                rmi.set_active(True)
            self.history_menu.append(rmi)

        self.history_menu.show_all()


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

        accel = Gtk.AccelGroup()
        self.add_accel_group(accel)
        self.search_entry.add_accelerator("grab_focus", accel, ord('f'), Gdk.ModifierType.CONTROL_MASK, 0)

        ## Search Button
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
                print("action: shift enter", file=fp3)
                state = self.toolbar.t_ShowAll.get_active()
                self.toolbar.t_ShowAll.set_active(not state)
                self.search_and_reflect()
                self.toolbar.t_ShowAll.set_active(not state)
        elif event.keyval == 65293: self.search_and_reflect() # <enter> return


    def makeWidgets_sidebar(self):
        self.sidebar = Side.Sidebar(self)
        treeselection = self.sidebar.treeview.get_selection()
        self.sidebar.select_signal = treeselection.connect("changed", self.sidebar_on_row_changed)

        for obj in self.sidebar.track_FONT:
            obj.modify_font(FONT_obj)
        return self.sidebar


    @debug
    def sidebar_on_row_changed(self, treeselection):
        model, pathlist = treeselection.get_selected_rows()
        self.clips.clear()
        for path in pathlist:
            self._view_item(*self.sidebar.get_suggestion(path))

        if len(self.clips) == 0: return
        self.clips_CYCLE = utils.circle(self.clips)
        self._circular_search(+1)


    def makeWidgets_viewer(self):
        self.viewer = Vi.Viewer(self)
        self.viewer.textview.modify_font(FONT_obj)
        self.track_FONT.add(self.viewer.textview)

        self.viewer.tb_clean.connect("clicked", self.viewer_clean)
        self.viewer.textview.connect("button-release-event", self.viewer_after_click)
        self.viewer.textview.connect("event", self.viewer_on_activity)
        return self.viewer


    def viewer_clean(self, widget=None):
        self.copy_BUFFER = ""
        self.view_CURRENT.clear()
        self.viewer.textbuffer.set_text("")
        selection = self.sidebar.treeview.get_selection()
        selection.unselect_all()


    def viewer_after_click(self, textview, eventbutton):
        mark = self.viewer.textbuffer.get_insert()
        end = self.viewer.textbuffer.get_iter_at_mark(mark)
        char = end.get_char()
        # print(end.get_offset())
        if not end.forward_word_end(): return
        begin = end.copy()
        if not begin.backward_word_start(): return
        word = self.viewer.textbuffer.get_text(begin, end, True)
        ## validate selectection
        if char not in word: return
        BEGIN = self.viewer.textbuffer.get_start_iter()
        END = self.viewer.textbuffer.get_end_iter()
        self.viewer.textbuffer.remove_tag(self.viewer.tag_found, BEGIN, END)
        self.viewer.textbuffer.apply_tag(self.viewer.tag_found, begin, end)
        self.toolbar.t_Copy.set_active(True)
        self.copy_BUFFER = word


    def viewer_on_activity(self, textview, event):
        if event.type == Gdk.EventType._2BUTTON_PRESS:
            bounds = self.viewer.textbuffer.get_selection_bounds()
            if not bounds: return
            begin, end = bounds
            query = self.viewer.textbuffer.get_text(begin, end, True)
            self.search_entry.set_text(query)
            self.search_and_reflect(query)


    def makeWidgets_relations(self):
        self.relatives = relations.Relatives()
        return self.relatives


    def get_active_query(self):
        selection = self.sidebar.treeview.get_selection()
        model, pathlst, = selection.get_selected_rows()

        if pathlst:
            *c, query = model[pathlst[0]]
        else:
            query = self.search_entry.get_text().strip().lower()

        return query


    def search_and_reflect(self, query=None):
        if query is None:
            query = self.search_entry.get_text()
            if not query: return

            for key, func in self.engines.items():
                if key == query[:2]: # raw mode
                    func(query)
                    return

        ## Ordered Dict use for undo/redo history
        query_RESULTS = OrderedDict()

        for w in set(query.split()):
            word = w.strip().lower()
            query_RESULTS[word] = core.Glossary.search(word)

        self._view_results(query_RESULTS)

        self.hist_LIST.append(query_RESULTS)
        self.hist_CURSOR = len(self.hist_LIST) - 1
        self.toolbar.bm_Backward.set_sensitive(True)
        self.toolbar.b_Forward.set_sensitive(False)


    def _view_item(self, instance, category, row):
        ID, word, info = row
        meta = (instance, category, ID)
        parsed_info = core.Glossary.format_parser(info)
        print(parsed_info, file=fp4)
        ## put trasliteration copy at last
        transliterate = []
        for pos, val in parsed_info:
            if   pos[0] == "_" or val == "": continue
            elif pos == "_transliterate": transliterate.append(val); continue
            self.clips.append(val)

        self.clips += transliterate

        if meta in self.view_CURRENT: return
        self.viewer.append_result(word, parsed_info, category)
        self.view_CURRENT.add(meta)


    @treeview_signal_safe_toggler
    def _view_results(self, query_RESULTS):
        self.sidebar.clear()
        self.clips.clear()
        treeselection = self.sidebar.treeview.get_selection()

        end = self.viewer.textbuffer.get_end_iter()
        begin = end.get_offset()

        all_FUZZ = []
        for word, (FULL, FUZZ) in query_RESULTS.items():
            all_FUZZ += FUZZ
            if not FULL:
                self.viewer.not_found(word)
                continue

            for item in FULL:
                self.sidebar.add_suggestion(*item)
                self._view_item(*item)
                treeselection.select_path(self.sidebar.count - 1)


        end = self.viewer.textbuffer.get_end_iter()
        self.mark_CURRENT = (begin, end.get_offset())
        self.viewer.jump_to_end()

        for item in sorted(all_FUZZ, key=lambda k: k[2][1]):
            self.sidebar.add_suggestion(*item)

        print("clip:", self.clips, file=fp3)
        if len(self.clips) == 0: return
        self.clips_CYCLE = utils.circle(self.clips)
        self._circular_search(+1)
        self.search_entry.grab_focus()


    @turn_off_auto_copy
    def _open_src(self):
        treeselection = self.sidebar.treeview.get_selection()
        model, pathlst = treeselection.get_selected_rows()

        line = -1
        if len(pathlst) == 0:
            path = core.Glossary.instances[0].categories['main'][-1]
        else:
            instance, path, row = self.sidebar.get_suggestion(pathlst[0])
            line = row[0]

        if EDITOR == "": return

        if EDITOR == "leafpad": command = EDITOR + " --jump=%d "%line
        elif EDITOR == "gedit": command = EDITOR + " +%d "%line
        else: command = EDITOR + " "

        command += path

        print("pid:", command, Popen(command.split()).pid, file=fp5)


    @turn_off_auto_copy
    def _open_dir(self):
        path = core.Glossary.instances[0].fullpath
        print("pid:", Popen(["nemo", path]).pid, file=fp5)


    def _circular_search(self, d):
        if not self.clips_CYCLE:
            self.search_entry.grab_focus()
            return

        self.toolbar.t_Copy.set_active(True)
        utils.diff = d
        text = next(self.clips_CYCLE)

        begin = self.viewer.textbuffer.get_start_iter()
        end = self.viewer.textbuffer.get_end_iter()

        self.viewer.textbuffer.remove_tag(self.viewer.tag_found, begin, end)
        position = self.viewer.mark_found(text, begin)
        m = self.viewer.textbuffer.create_mark("tmp", position)
        self.viewer.textview.scroll_mark_onscreen(m)
        self.viewer.textbuffer.delete_mark(m)
        self.copy_BUFFER = text


    @turn_off_auto_copy
    def add_to_gloss(self, query=""):
        add = Ad.Add(self, l1=query, l2="")
        for obj in add.track_FONT:
            obj.modify_font(FONT_obj)
        # TODO: connection
        add.connect('destroy', self._add_to_gloss_reflect)


    def _add_to_gloss_reflect(self, *args):
        print("hello i'm back", file=fp5)


    def preference(self, query=""):
        Pre.def_FONT = def_FONT
        s = Pre.Settings(self)


    def key_binds(self, widget, event):
        keyval, state = event.keyval, event.state
        if   keyval == 65362: self.sidebar.treeview.grab_focus() # Up-arrow
        elif keyval == 65364: self.sidebar.treeview.grab_focus() # Down-arrow
        elif Gdk.ModifierType.CONTROL_MASK & state:
            if   keyval == ord('e'): self._open_src()
            # elif keyval == ord('i'): self.add_to_gloss()
            elif keyval == ord('l'): self.viewer_clean()
            elif keyval == ord('r'): self._circular_search(-1)
            elif keyval == ord('s'): self._circular_search(+1)
            elif keyval == ord('g'): # grab clipboard
                clip = __class__.clipboard.wait_for_text()
                if clip is None: return
                query = clip.strip().lower()
                self.search_entry.set_text(clip)
                self.search_and_reflect()
            return
        elif Gdk.ModifierType.MOD1_MASK & state:
            if   keyval == 65361: self._jump_history(-1) # Left-arrow
            elif keyval == 65363: self._jump_history(+1) # Right-arrow
            return
        elif Gdk.ModifierType.SHIFT_MASK & event.state:
            # TODO Scroll viewer
            if   keyval == 65365: pass # Pg-Dn
            elif keyval == 65366: pass # Pg-Up
            return

        if event.keyval in ignore_keys: return
        if self.search_entry.is_focus(): return

        self.search_entry.grab_focus()
        pos = self.search_entry.get_position()
        self.search_entry.set_position(pos + 1)
        self.search_entry_binds(widget, event)


def init():
    # import __main__
    # TODO where to add __main__function
    core.fp3 = fp5
    core.fp4 = fp6
    Vi.PWD = PWD

    global PATH_GLOSS
    core.PATH_GLOSS = PATH_GLOSS = PWD + PATH_GLOSS

    global FONT_obj
    FONT_obj = Pango.font_description_from_string(def_FONT)
    browser.FONT_obj = FONT_obj
    browser.fp3 = fp4

    # MAYBE do __main__ import here

    global BROWSER
    Vi.BROWSER = BROWSER

    global ignore_keys
    ignore_keys = [ v for k, v in utils.key_codes.items() if v != utils.key_codes["RETURN"]]

    for path in LIST_GLOSS:
        core.Glossary(path)


def main():
    init()
    root = GUI()
    notebook = browser.Notebook(core.Glossary.instances[0], root)
    root.layout.attach(notebook, 0, 7, 5, 2)
    return root


if __name__ == '__main__':
    main()
    Gtk.main()
