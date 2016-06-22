#!/usr/bin/env python3

import os, sys

__filepath__ = os.path.abspath(__file__)
sys.path.append(os.path.dirname(__filepath__))

fp3 = fp4 = sys.stderr

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Pango
from gi.repository import GObject

from multiprocessing.pool import ThreadPool
from collections import OrderedDict

import searchbar
import sidebar
import view
import relations

def treeview_signal_safe_toggler(func):
    '''Gtk.TreeView() :changed: signal should be disable before new
    selection is added, if connect it will trigger the change.

    '''
    def wrapper(self, *args, **kwargs):
        treeSelection = self.sidebar.treeview.get_selection()
        treeSelection.disconnect(self.sidebar.select_signal)
        func_return = func(self, *args, **kwargs)
        self.sidebar.select_signal = treeSelection.connect("changed", self.sidebar_on_row_changed)
        return func_return
    return wrapper


def circle(iterable):
    if not hasattr(circle, 'DIFF'): # cool static var
        circle.DIFF = 1
    saved = iterable[:]
    i = -1
    while saved:
        l = len(saved)
        i += circle.DIFF
        if circle.DIFF == +1 and l <= i: i = 0
        if circle.DIFF == -1 and i <  0: i = l - 1
        yield saved[i]


class Home(Gtk.Window):
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

    def __init__(self, core, cnf):
        Gtk.Window.__init__(self, name="Home")

        self.core     = core
        self.tray     = cnf.preferences['show-on-system-tray']
        self.nothread = cnf.core['no-thread']

        self.fonts = {
            'viewer': Pango.font_description_from_string(cnf.fonts['viewer']),
            'search': Pango.font_description_from_string(cnf.fonts['viewer']),
        }

        self.track_FONT = set()

        self.clips = []
        self.clips_circle = None

        self.view_current = set()

        self.cache = []
        self.cache_cursor = 0
        self.copy_buffer = ""

        self.pool = ThreadPool(processes=1)

        self.engines = [ # not using dict() since we are traversing it
            (lambda q: q[0] == '#',  self.core.Glossary.search_hashtag),
            (lambda q: q[0] == '\\', lambda q: self.core.Glossary.search(q[1:])),
        ]

        # accelerators
        self.makeWidgets()
        self.connect('key_press_event', self.on_key_press)
        self.connect('key_release_event', self.on_key_release)
        self.connect('focus-in-event', lambda *e: self.searchbar.entry.grab_focus())
        self.connect('focus-out-event', lambda *e: self._on_focus_out_event())

        self.searchbar.entry.grab_focus()
        # gdk_window = self.get_root_window()
        # gdk_window.set_cursor(Gdk.Cursor(Gdk.CursorType.WATCH))
        self.set_default_size(600, 550)
        self.set_position(Gtk.WindowPosition.CENTER)


    def _on_focus_out_event(self):
        if self.toolbar.t_COPY.get_active():
            __class__.clipboard.set_text(self.copy_buffer, -1)


    def engine_default(self, query):
        ## Ordered Dict use for undo/redo history
        results = OrderedDict()
        for q in query.split():
            word = q.lower()
            for history in self.cache:
                if word in history.keys():
                    print("cache: hit", word, file=fp3)
                    results[word] = history[word]
                    continue

            results[word] = self.core.Glossary.search(word)

        self.cache.append(results)
        self.cache_cursor = len(self.cache) - 1
        self.toolbar.mb_BACKWARD.set_sensitive(True)
        self.toolbar.b_FORWARD.set_sensitive(False)
        return results


    def makeWidgets(self):
        self.layout = Gtk.Grid(orientation=1)
        self.add(self.layout)

        self.toolbar = self.makeWidgets_toolbar()
        self.layout.add(self.toolbar)

        self.layout.add(self.makeWidgets_searchbar())

        hpaned = Gtk.Paned()
        self.layout.add(hpaned)

        hpaned.add1(self.makeWidgets_sidebar())
        hpaned.add2(self.makeWidgets_viewer())
        hpaned.set_position(165)

        self.relations = self.makeWidgets_relations()
        self.layout.add(self.relations)
        self.relations.set_hexpand(True)
        self.layout.show_all()

        self.infobar = Gtk.InfoBar()
        self.layout.add(self.infobar)

        self.infobar.LABEL = Gtk.Label()
        content = self.infobar.get_content_area()
        content.add(self.infobar.LABEL)

        self.infobar.set_show_close_button(True)
        self.infobar.set_default_response(Gtk.ResponseType.CLOSE)
        self.infobar.connect("response", lambda w, id: w.hide())


    def makeWidgets_toolbar(self):
        bar = Gtk.Toolbar()
        #
        ## Button Back Button
        bar.mb_BACKWARD = Gtk.MenuToolButton(icon_name="go-previous")
        bar.add(bar.mb_BACKWARD)
        bar.mb_BACKWARD.connect("clicked", lambda e: self._jump_history(-1))
        bar.mb_BACKWARD.set_tooltip_markup("Previous, <u>Alt+←</u>")
        bar.mb_BACKWARD.set_sensitive(False)
        ### History
        # TODO: find the widget flag
        self.hist_menu_toggle_state = False
        self.history_menu = Gtk.Menu() # NOTE: DUMMY MENU For Menu activation
        bar.mb_BACKWARD.set_menu(self.history_menu)
        bar.mb_BACKWARD.connect("show-menu", lambda e: self._show_history(e))
        ##
        ## Button Forward Button
        bar.b_FORWARD = Gtk.ToolButton(icon_name="go-next")
        bar.add(bar.b_FORWARD)
        bar.b_FORWARD.connect("clicked", lambda e: self._jump_history(+1))
        bar.b_FORWARD.set_tooltip_markup("Next, <u>Alt+→</u>")
        bar.b_FORWARD.set_sensitive(False)
        ##
        #
        bar.add(Gtk.SeparatorToolItem())
        ##
        ## Smart Copy Toggle Button
        bar.t_COPY = Gtk.ToggleToolButton(icon_name='edit-copy')
        bar.add(bar.t_COPY)
        bar.t_COPY.set_active(True)
        ##
        ## Add Button
        bar.b_ADD = Gtk.ToolButton(icon_name="list-add")
        bar.add(bar.b_ADD)
        # bar.b_ADD.connect("clicked", lambda w: self.add_to_gloss())
        bar.b_ADD.set_tooltip_markup("Add new word to Glossary, <u>Ctrl+i</u>")
        ##
        #
        bar.s_END = Gtk.SeparatorToolItem()
        bar.add(bar.s_END)
        return bar


    def _jump_history(self, diff):
        pos = self.cache_cursor + diff

        if 0 > pos: return
        elif len(self.cache) <= pos:
            self.toolbar.b_FORWARD.set_sensitive(False)
            return

        if diff == -1: self.toolbar.b_FORWARD.set_sensitive(True)

        self.cache_cursor = pos
        self._view_results(self.cache[pos])


    def _show_history(self, widget):
        state = self.hist_menu_toggle_state
        self.hist_menu_toggle_state = not state
        if state: return

        del self.history_menu
        self.history_menu = Gtk.Menu()
        widget.set_menu(self.history_menu)

        for i, results in enumerate(reversed(self.cache), 1):
            query = ', '.join([ k for k in results.keys() ])
            rmi = Gtk.RadioMenuItem(label=query)
            rmi.show()
            if len(self.cache) - i == self.cache_cursor:
                rmi.set_active(True)
            self.history_menu.append(rmi)

        self.history_menu.show_all()


    def makeWidgets_searchbar(self):
        self.searchbar = searchbar.Bar()
        self.searchbar.button.connect('clicked', lambda *a: self.search_and_reflect())

        #### liststore
        # BUG: left cell align is not working, so "%4d"
        liststore = Gtk.ListStore(str, str)
        for k, v in sorted(self.core.Glossary.hashtags.items()):
            liststore.append([k, "%4d"%v])

        self.searchbar.add_hashtag_completion(liststore)

        def _on_key_press(widget, event):
            if event.keyval == 65289: # Tab
                self.sidebar.treeview.grab_focus()
                return True
            elif Gdk.ModifierType.CONTROL_MASK & event.state:
                if event.keyval == ord('c'):
                    if widget.get_selection_bounds():
                        self.toolbar.t_COPY.set_active(False)
                        return
                    widget.set_text("")

        self.searchbar.entry.connect('key_press_event', _on_key_press)

        def _on_key_release(widget, event):
            # NOTE to stop propagation of signal return True
            if   event is None: self.search_and_reflect()
            elif event.keyval == 65293: self.search_and_reflect() # <enter> return

        self.searchbar.entry.connect('key_release_event', _on_key_release)

        self.searchbar.entry.modify_font(self.fonts['search'])
        self.track_FONT.add(self.searchbar.entry)
        return self.searchbar



    def makeWidgets_sidebar(self):
        self.sidebar = sidebar.Bar(self)
        treeSelection = self.sidebar.treeview.get_selection()
        self.sidebar.select_signal = treeSelection.connect("changed", self.sidebar_on_row_changed)

        def _on_key_press(widget, event):
            # NOTE to stop propagation of signal return True
            if event.keyval == 65289: # Tab
                self.searchbar.entry.grab_focus()
                return True

        self.sidebar.connect("key_press_event", _on_key_press)

        for obj in self.sidebar.track_FONT:
            obj.modify_font(self.fonts['viewer'])
        return self.sidebar


    def sidebar_on_row_changed(self, treeSelection):
        model, pathlist = treeSelection.get_selected_rows()
        self.clips.clear()
        for path in pathlist:
            self._view_item(*self.sidebar.get_suggestion(path))

        if len(self.clips) == 0: return
        self.clips_circle = circle(self.clips)
        self._circular_search(+1)


    def makeWidgets_viewer(self):
        self.viewer = view.Display(self)
        self.viewer.textview.modify_font(self.fonts['viewer'])
        self.track_FONT.add(self.viewer.textview)

        self.viewer.tb_clean.connect("clicked", self.viewer_clean)
        self.viewer.textview.connect("button-release-event", self.viewer_after_click)
        self.viewer.textview.connect("event", self.viewer_on_activity)
        return self.viewer


    def viewer_clean(self, widget=None):
        if self.viewer.textbuffer.get_char_count() > 1:
            self.copy_buffer = ""
            self.clips_circle = None
            self.view_current.clear()
            self.viewer.textbuffer.set_text("\n")
            treeSelection = self.sidebar.treeview.get_selection()
            treeSelection.unselect_all()
            return

        self.sidebar.clear()
        self.clips.clear()


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
        self.toolbar.t_COPY.set_active(True)
        self.copy_buffer = text


    def viewer_on_activity(self, textview, event):
        if event.type != Gdk.EventType._2BUTTON_PRESS: return
        bounds = self.viewer.textbuffer.get_selection_bounds()
        if not bounds: return
        begin, end = bounds
        query = self.viewer.textbuffer.get_text(begin, end, True)
        self.searchbar.entry.set_text(query)
        self.search_and_reflect(query)


    def makeWidgets_relations(self):
        self.relatives = relations.Relatives()
        return self.relatives


    def get_active_query(self):
        treeSelection = self.sidebar.treeview.get_selection()
        model, pathlst, = treeSelection.get_selected_rows()

        if pathlst:
            *c, query = model[pathlst[0]]
        else:
            query = self.searchbar.entry.get_text().strip().lower()

        return query


    def do_search_pulse(self, query, async_ret):
        """Search Pulse Function

        Executing the Gtk.TextViewer in threading crashes. To avoid
        crashing remaining segment which make changes in
        Gtk.TextViewer is moved out of thread and executed after
        results are ready.

        """
        self.searchbar.entry.progress_pulse()
        if not async_ret.ready(): return True
        self.fit_output(query, async_ret.get())
        self.searchbar.entry.set_progress_fraction(0)
        return False


    def search_and_reflect(self, query=None):
        if query is None:
            query = self.searchbar.entry.get_text()

        if not query: return

        self.searchbar.entry.HISTORY.append(query)
        self.searchbar.entry.CURRENT = len(self.searchbar.entry.HISTORY)

        # choosing engines
        engine = self.engine_default
        for test, func in self.engines:
            if test(query):
                engine = func
                break

        if self.nothread:
            self.fit_output(query, engine(query))
            return

        async_ret = self.pool.apply_async(engine, (query,))
        timeout_id = GObject.timeout_add(400, self.do_search_pulse, query, async_ret)


    def fit_output(self, query, output):
        if output is None:
            self.infobar.LABEL.set_markup("<b>%s</b> did not gave any output"%query)
            self.infobar.show_all()
            return

        if type(output) == tuple: return self._view_results({ query: output })
        if type(output) == str:
            begin = self.viewer.textbuffer.get_start_iter()
            self.viewer.textbuffer.place_cursor(begin)
            self.viewer.insert_at_cursor("\n")
            if output != '':
                self.viewer.insert_at_cursor(output)
                return

            self.infobar.LABEL.set_markup("<b>%s</b> did not gave any output"%query)
            self.infobar.show_all()
            return

        self._view_results(output)


    @treeview_signal_safe_toggler
    def _view_results(self, results):
        self.sidebar.clear()
        self.clips.clear()
        treeSelection = self.sidebar.treeview.get_selection()

        begin = self.viewer.textbuffer.get_start_iter()
        self.viewer.textbuffer.place_cursor(begin)
        self.viewer.textbuffer.insert_at_cursor("\n")

        all_FUZZ = dict()
        for word, (FULL, FUZZ) in results.items():
            all_FUZZ.update(FUZZ)
            if not FULL:
                self.viewer.not_found(word)
                continue

            for key, val in FULL.items():
                self.sidebar.add_suggestion(key, val)
                word, ID, src = key
                # NOTE: unpacking variable, seems some python version
                # only supports named args followed by *expression
                # ref: https://github.com/foss-np/anubad/issues/11
                self._view_item(word, ID, src, val)
                treeSelection.select_path(self.sidebar.count - 1)

        self.viewer.textbuffer.insert_at_cursor("\n")
        self.viewer.jump_to_top()

        for key in sorted(all_FUZZ, key=lambda k: k[0]):
            self.sidebar.add_suggestion(key, all_FUZZ[key])

        if len(self.clips) == 0: return
        print("clip:", self.clips, file=fp4)
        self.clips_circle = circle(self.clips)
        self._circular_search(+1)
        self.searchbar.entry.grab_focus()


    def _view_item(self, word, ID, src, parsed_info):
        print(parsed_info, file=fp4)
        meta = (word, ID, src)

        ## put trasliteration at last
        transliterate = [] # collect trasliterations

        for pos, val in parsed_info:
            if   pos == "_transliterate": transliterate.append(val); continue
            elif pos[0] == "_" or val == "": continue
            self.clips.append(val)

        ## adding transliteration
        self.clips += transliterate

        if meta in self.view_current:
            print("already in view:", meta, file=fp3)
            return

        self.viewer.insert_result(word, parsed_info, src)
        self.view_current.add(meta)


    def _circular_search(self, diff):
        if not self.clips_circle:
            self.searchbar.entry.grab_focus()
            return

        self.toolbar.t_COPY.set_active(True)
        circle.DIFF = diff
        text = next(self.clips_circle)

        ## highlight current clip
        ## TODO only highlight new search item
        begin, end = self.viewer.clean_highlights()
        start, stop = self.viewer.find_and_highlight(text, begin)
        self.viewer.jump_to(start)
        self.copy_buffer = text


    def handle_esc(self):
        if self.tray:
            self.hide()
            return

        self.iconify()


    def on_key_press(self, widget, event):
        # NOTE to stop propagation of signal return True
        if  Gdk.ModifierType.CONTROL_MASK & event.state:
            if event.keyval == 65379: # Insert
                if    self.viewer.textbuffer.get_selection_bounds(): self.toolbar.t_COPY.set_active(False)
                elif  self.searchbar.entry.get_selection_bounds()  : self.toolbar.t_COPY.set_active(False)
                else: self._circular_search(+1)
            elif event.keyval == ord('b'): self._circular_search(+1)
            elif event.keyval == ord('B'): self._circular_search(-1)
            return
        elif Gdk.ModifierType.SHIFT_MASK & event.state:
            if   event.keyval == 65365: self._circular_search(-1); return True # Pg-Up
            elif event.keyval == 65366: self._circular_search(+1); return True # Pg-Dn
        elif event.keyval == 65307: return self.handle_esc() # Esc
        elif event.keyval == 65365: self.viewer.textview.grab_focus(); return # Pg-Up
        elif event.keyval == 65366: self.viewer.textview.grab_focus(); return # Pg-Dn

        if self.searchbar.entry.is_focus(): return

        if event.keyval > 127: return # ignore non-printable values
        self.searchbar.entry.grab_focus()
        pos = self.searchbar.entry.get_position()
        self.searchbar.entry.set_position(pos + 1)


    def on_key_release(self, widget, event):
        # NOTE to stop propagation of signal return True
        if   event.keyval == 65474: self.core.Glossary.reload() # F5
        # TODO: exception handeling
        # NOTE: ^^^^ this does'nt reload the hashtags to entry
        elif Gdk.ModifierType.CONTROL_MASK & event.state:
            if   event.keyval == ord('l'): self.viewer_clean()
            elif event.keyval == ord('q'): self.emit("delete-event", Gdk.Event.new(Gdk.EventType.DELETE))
            elif event.keyval == ord('Q'): self.emit("delete-event", Gdk.Event.new(Gdk.EventType.DELETE))
            elif event.keyval == ord('x'): self.emit("delete-event", Gdk.Event.new(Gdk.EventType.DELETE))
            elif event.keyval == ord('X'): self.emit("delete-event", Gdk.Event.new(Gdk.EventType.DELETE))
            elif event.keyval == ord('g'): # grab clipboard
                clip = __class__.clipboard.wait_for_text()
                if clip is None: return
                query = clip.strip().lower()
                self.searchbar.entry.set_text(clip)
                self.search_and_reflect(clip)
        elif Gdk.ModifierType.MOD1_MASK & event.state:
            if   event.keyval == 65361: self._jump_history(-1) # Left-arrow
            elif event.keyval == 65363: self._jump_history(+1) # Right-arrow
            elif event.keyval == ord('x'):
                self.searchbar.entry.set_text("> ")
                self.searchbar.entry.set_position(2)



def main(core, cnf):
    win = Home(core, cnf)
    win.show()
    return win


def sample():
    sys.path.append(sys.path[0]+'/../')
    import setting
    import core
    core.fp3 = core.fp4 = open(os.devnull, 'w')

    cnf = setting.main()
    core.load_from_config(cnf)

    root = main(core, cnf)
    root.connect('delete-event', Gtk.main_quit)

    # in isolation testing, make Esc quit Gtk mainloop
    root.handle_esc = Gtk.main_quit


if __name__ == '__main__':
    sample()
    Gtk.main()
