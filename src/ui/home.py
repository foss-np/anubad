#!/usr/bin/env python3

import os, sys

__filepath__ = os.path.abspath(__file__)
PWD = os.path.dirname(__filepath__) + '/../'

sys.path.append(PWD)

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Gio, Pango

from collections import OrderedDict
from subprocess import Popen
from itertools import count

import utils
import ui.preferences
import ui.sidebar
import ui.view
import ui.relations

key_codes = {
    "BACKSPACE"     : 65288,
    "RETURN"        : 65293,
    "ESCAPE"        : 65307,

    "LEFT_ARROW"    : 65361,
    "UP_ARROW"      : 65362,
    "RIGHT_ARROW"   : 65363,
    "DOWN_ARROW"    : 65364,

    "MENU"          : 65383,
    "PAGE_UP"       : 65365,
    "PAGE_UP"       : 65366,

    "F1"            : 65470,
    "F2"            : 65471,
    "F3"            : 65472,
    "F3"            : 65473,
    "F5"            : 65474,
    "F6"            : 65475,
    "F7"            : 65476,
    "F8"            : 65477,
    "F9"            : 65478,
    "F10"           : 65479,
    "F11"           : 65480,
    "F12"           : 65481,

    "SHIFT_LEFT"    : 65505,
    "SHIFT_RIGHT"   : 65506,
    "CONTROL_LEFT"  : 65507,
    "CONTROL_RIGHT" : 65508,
    "ALT_LEFT"      : 65513,
    "ALT_RIGHT"     : 65514,
    "META"          : 65515,
    "DELETE"        : 65535,
}

ignore_keys = [ v for k, v in key_codes.items() if v != key_codes["RETURN"]]

fp_dev_null = open(os.devnull, 'w')
VERBOSE = int(os.environ.get("VERBOSE", 0))
for i in range(3, 7):
    if VERBOSE > 0:
        print(
            "VERBOSE: %d fp%d enabled"%(VERBOSE, i),
            file=sys.stderr
        )
        stream = "sys.stderr"
        VERBOSE -= 1
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


class Home(Gtk.Window):
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

    def __init__(self, core, rc, app=None):
        Gtk.Window.__init__(
            self,
            type=Gtk.WindowType.TOPLEVEL,
            application=app
        )

        self.core = core
        self.rc   = rc
        self.app  = app

        self.fonts = {
            'viewer': Pango.font_description_from_string(rc.fonts['viewer']),
            'search': Pango.font_description_from_string(rc.fonts['viewer']),
        }

        self.track_FONT = set()

        self.clips = []
        self.clips_CYCLE = None

        self.view_CURRENT = set()

        self.hist_LIST = []
        self.hist_CURSOR = 0
        self.copy_BUFFER = ""

        self.engines = [ # not using dict() since we are traversing it
            (lambda q: q[0] == '#',  core.Glossary.search_hashtag),
            (lambda q: q[0] == '\\', lambda q: core.Glossary.search(q[1:])),
        ]

        # accelerators
        self.makeWidgets()
        self.connect('key_press_event', self.key_press_binds)
        self.connect('key_release_event', self.key_release_binds)
        self.connect('focus-in-event', lambda *e: self.search_entry.grab_focus())
        self.connect('focus-out-event', lambda *e: self._on_focus_out_event())
        self.connect('delete-event', self.on_destroy)

        self.search_entry.grab_focus()
        # gdk_window = self.get_root_window()
        # gdk_window.set_cursor(Gdk.Cursor(Gdk.CursorType.WATCH))
        self.set_default_size(600, 550)
        self.set_position(Gtk.WindowPosition.CENTER)


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

        self.relations = self.makeWidgets_relations()
        self.layout.attach(self.relations, left=0, top=5, width=5, height=2)


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
        ##
        ## Smart Copy Toggle Button
        bar.t_Copy = Gtk.ToggleToolButton(icon_name=Gtk.STOCK_COPY)
        bar.add(bar.t_Copy)
        bar.t_Copy.set_active(True)
        ##
        ## Add Button
        bar.b_Add = Gtk.ToolButton(icon_name=Gtk.STOCK_ADD)
        bar.add(bar.b_Add)
        # bar.b_Add.connect("clicked", lambda w: self.add_to_gloss())
        bar.b_Add.set_tooltip_markup("Add new word to Glossary, <u>Ctrl+i</u>")
        ##
        #
        ##  Preference
        bar.b_Preference = Gtk.ToolButton(icon_name=Gtk.STOCK_PREFERENCES)
        bar.add(bar.b_Preference)
        bar.b_Preference.connect("clicked", self.preference)
        bar.b_Preference.set_tooltip_markup("Preferences")
        ##
        #
        bar.s_end = Gtk.SeparatorToolItem()
        bar.add(bar.s_end)
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

        ## Label
        label = Gtk.Label()
        label.set_markup("<b>Query</b>")
        layout.pack_start(label, expand=False, fill=False, padding=60)

        ## Entry
        tool_tip = "<b>Search:</b> \t⌨ [<i>Enter</i>]"
        self.search_entry = Gtk.SearchEntry()
        layout.pack_start(self.search_entry, expand=True, fill=True, padding=2)
        ### liststore
        liststore = Gtk.ListStore(str, str)
        # NOTE: second variable to do the split match, and optimization
        for item in sorted(self.core.Glossary.hashtag):
            liststore.append([item, item.replace('.', '#')])
        ### entrycomplete
        entrycompletion = Gtk.EntryCompletion()
        self.search_entry.set_completion(entrycompletion)
        entrycompletion.set_model(liststore)
        entrycompletion.set_text_column(0)
        # entrycompletion.insert_action_markup(0, "<b><i>#Hashtag</i> Search</b>")
        # NOTE: func only for exact match, but we have fuzzy
        ## entrycompletion.set_inline_completion(False) # default:0
        ## entrycompletion.set_popup_single_match(True) # default:1

        def _match_func(gobj_completion, query, treeiter, liststore):
            if not query[0] == '#': return False
            model = entrycompletion.get_model()[treeiter][1]
            return query in model

        entrycompletion.set_match_func(_match_func, liststore)
        ### options
        self.search_entry.connect('key_release_event', self.search_entry_binds)
        self.search_entry.set_tooltip_markup(tool_tip)
        self.search_entry.set_max_length(32)
        ### font
        self.search_entry.modify_font(self.fonts['search'])
        self.track_FONT.add(self.search_entry)
        ### acceleration
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
        elif event.keyval == 65293: self.search_and_reflect() # <enter> return


    def makeWidgets_sidebar(self):
        self.sidebar = ui.sidebar.Bar(self)
        treeselection = self.sidebar.treeview.get_selection()
        self.sidebar.select_signal = treeselection.connect("changed", self.sidebar_on_row_changed)

        for obj in self.sidebar.track_FONT:
            obj.modify_font(self.fonts['viewer'])
        return self.sidebar


    def sidebar_on_row_changed(self, treeselection):
        model, pathlist = treeselection.get_selected_rows()
        self.clips.clear()
        for path in pathlist:
            self._view_item(*self.sidebar.get_suggestion(path))

        if len(self.clips) == 0: return
        self.clips_CIRCLE = utils.circle(self.clips)
        self._circular_search(+1)


    def makeWidgets_viewer(self):
        self.viewer = ui.view.Display(self, PWD)
        self.viewer.textview.modify_font(self.fonts['viewer'])
        self.track_FONT.add(self.viewer.textview)

        self.viewer.tb_clean.connect("clicked", self.viewer_clean)
        self.viewer.textview.connect("button-release-event", self.viewer_after_click)
        self.viewer.textview.connect("event", self.viewer_on_activity)
        return self.viewer


    def viewer_clean(self, widget=None):
        self.copy_BUFFER = ""
        self.clips_CIRCLE = None
        self.view_CURRENT.clear()
        self.viewer.textbuffer.set_text("\n")
        selection = self.sidebar.treeview.get_selection()
        selection.unselect_all()


    def viewer_after_click(self, textview, eventbutton):
        bound = self.viewer.textbuffer.get_selection_bounds()
        if bound:
            begin, end = bound
            text = self.viewer.textbuffer.get_text(begin, end, True)
        else:
            word_obj = self.viewer.get_wordObj_at_cursor()
            if word_obj is None: return
            text, begin, end = word_obj

        ## highlight
        self.viewer.clean_highlights()
        self.viewer.textbuffer.apply_tag(self.viewer.tag_found, begin, end)
        self.toolbar.t_Copy.set_active(True)
        self.copy_BUFFER = text


    def viewer_on_activity(self, textview, event):
        if event.type != Gdk.EventType._2BUTTON_PRESS: return
        bounds = self.viewer.textbuffer.get_selection_bounds()
        if not bounds: return
        begin, end = bounds
        query = self.viewer.textbuffer.get_text(begin, end, True)
        self.search_entry.set_text(query)
        self.search_and_reflect(query)


    def makeWidgets_relations(self):
        self.relatives = ui.relations.Relatives()
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

        # choosing alternative engines
        for test, func in self.engines:
            if test(query):
                print("engine called", file=fp3)
                self._view_results({ query: func(query) })
                return

        ## Ordered Dict use for undo/redo history
        query_RESULTS = OrderedDict()
        for w in set(query.split()):
            word = w.strip().lower()
            # TODO: check if its in view && the glossary is changed
            for history in self.hist_LIST:
                if word in history.keys():
                    # print("found in hist cache")
                    query_RESULTS[word] = history[word]
                    continue

            query_RESULTS[word] = self.core.Glossary.search(word)

        self._view_results(query_RESULTS)

        self.hist_LIST.append(query_RESULTS)
        self.hist_CURSOR = len(self.hist_LIST) - 1
        self.toolbar.bm_Backward.set_sensitive(True)
        self.toolbar.b_Forward.set_sensitive(False)


    def _view_item(self, word, ID, path, parsed_info):
        """
        >>> root._view_item(instance, src, [1, "sunday" "[सन्डे] n(आइतबार) #time"])
        >>> print(GUI.clips)
        ['आइतबार', 'सन्डे'],
        """
        # TODO: move it to viewer
        print(parsed_info, file=fp4)
        meta = (word, ID, path)

        ## put trasliteration at last
        transliterate = [] # collect trasliterations

        for pos, val in parsed_info:
            if   pos == "_transliterate": transliterate.append(val); continue
            elif pos[0] == "_" or val == "": continue
            self.clips.append(val)

        ## adding transliteration
        self.clips += transliterate

        if meta in self.view_CURRENT:
            print("already in view:", meta, file=fp3)
            return
        self.viewer.insert_result(word, parsed_info, path)
        self.view_CURRENT.add(meta)


    @treeview_signal_safe_toggler
    def _view_results(self, query_RESULTS):
        self.sidebar.clear()
        self.clips.clear()
        treeselection = self.sidebar.treeview.get_selection()

        begin = self.viewer.textbuffer.get_start_iter()
        self.viewer.textbuffer.place_cursor(begin)
        self.viewer.textbuffer.insert_at_cursor("\n")

        all_FUZZ = dict()
        for word, (FULL, FUZZ) in query_RESULTS.items():
            all_FUZZ.update(FUZZ)
            if not FULL:
                self.viewer.not_found(word)
                continue

            for key, val in FULL.items():
                self.sidebar.add_suggestion(key, val)
                self._view_item(*key, val)
                treeselection.select_path(self.sidebar.count - 1)

        self.viewer.textbuffer.insert_at_cursor("\n")
        self.viewer.jump_to_top()

        for key in sorted(all_FUZZ, key=lambda k: k[0]):
            self.sidebar.add_suggestion(key, all_FUZZ[key])

        if len(self.clips) == 0: return
        print("clip:", self.clips, file=fp3)
        self.clips_CIRCLE = utils.circle(self.clips)
        self._circular_search(+1)
        self.search_entry.grab_focus()


    @turn_off_auto_copy
    def _open_src(self):
        treeselection = self.sidebar.treeview.get_selection()
        model, pathlst = treeselection.get_selected_rows()

        if len(pathlst) == 0:
            path = self.core.Glossary.instances[0].categories['main'][-1]
            line = self.core.Glossary.instances[0].entries
        else:
            word, ID, path, parsed_info  = self.sidebar.get_suggestion(pathlst[0])
            # print(row, file=fp6)

            ## handel invert map
            if type(ID) == int: line = ID
            else: # else tuple
                try:
                    i = self.clips.index(self.copy_BUFFER)
                    # print(i, file=fp6)
                    # print(ID, i)
                    line = ID[i]
                except ValueError:
                    line = None

        cmd = self.rc.editor_goto_line_uri(path, line)
        print("pid:", path, Popen(cmd).pid, file=fp5)


    def _circular_search(self, d):
        if not self.clips_CIRCLE:
            self.search_entry.grab_focus()
            return

        self.toolbar.t_Copy.set_active(True)
        utils.diff = d
        text = next(self.clips_CIRCLE)

        ## highlight current clip
        begin, end = self.viewer.clean_highlights()
        start, stop = self.viewer.find_and_highlight(text, begin)
        self.viewer.jump_to(start)
        self.copy_BUFFER = text


    @turn_off_auto_copy
    def add_to_gloss(self, query=""):
        widget = add.Add(self, l1=query, l2="")
        for obj in widget.track_FONT:
            obj.modify_font(FONT_obj)
        # TODO: connection
        widget.connect('destroy', self._add_to_gloss_reflect)


    def _add_to_gloss_reflect(self, *args):
        print("hello i'm back", file=fp5)


    def preference(self, widget):
        s = ui.preferences.Settings(self.rc, parent=self)
        s.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        s.show_all()


    # def do_delete_event(self, event):
    def on_destroy(self, event, *args):
        """Override the default handler for the delete-event signal"""
        # Show our message dialog
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            buttons=Gtk.ButtonsType.OK_CANCEL
        )

        dialog.props.text = 'Are you sure you want to quit?'
        def key_release_binds(widget, event):
            if Gdk.ModifierType.CONTROL_MASK & event.state:
                if event.keyval == ord('q'):
                    dialog.destroy()
                    self.destroy()
                    Gtk.main_quit()

        dialog.connect('key_release_event', key_release_binds)

        response = dialog.run()
        dialog.destroy()

        if response == Gtk.ResponseType.OK:
            return False

        return True


    def handle_esc(self):
        if self.rc.preferences['show-in-system-tray']:
            self.hide()
            return

        self.iconify()


    def key_press_binds(self, widget, event):
        if   event.keyval == 65362: self.sidebar.treeview.grab_focus() # Up-arrow
        elif event.keyval == 65364: self.sidebar.treeview.grab_focus() # Down-arrow
        elif event.keyval == 65307: # Esc
            self.handle_esc()


    def key_release_binds(self, widget, event):
        # TODO reload restart key
        keyval, state = event.keyval, event.state
        if  Gdk.ModifierType.CONTROL_MASK & state:
            if   keyval == ord('e'): self._open_src()
            elif keyval == ord('l'): self.viewer_clean()
            elif keyval == ord('q'): self.emit("delete-event", Gdk.Event.new(Gdk.EventType.DELETE))
            elif keyval == ord('r'): self._circular_search(-1)
            elif keyval == ord('s'): self._circular_search(+1)
            elif keyval == ord('g'): # grab clipboard
                clip = __class__.clipboard.wait_for_text()
                if clip is None: return
                query = clip.strip().lower()
                self.search_entry.set_text(clip)
                self.search_and_reflect(clip)
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


def main(core, rc, app=None):
    core.fp3 = fp5
    core.fp4 = fp6
    core.load_from_config(rc)

    root = Home(core, rc, app)
    root.show_all()
    return root


if __name__ == '__main__':
    import core

    import config
    rc = config.main(PWD)

    root = main(core, rc)
    root.connect('delete-event', Gtk.main_quit)

    # in isolation testing, make Esc quit Gtk mainloop
    root.handle_esc = Gtk.main_quit
    Gtk.main()
