#!/usr/bin/env python3

import os, sys

__filepath__ = os.path.abspath(__file__)
sys.path.append(os.path.dirname(__filepath__))

fp3 = fp4 = sys.stderr

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from gi.repository import GObject

from multiprocessing.pool import ThreadPool
from collections import OrderedDict

import _searchbar
import _sidebar
import _view
import _relations

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

        self.core             = core
        self.PWD              = cnf.PWD
        self.tray             = cnf.preferences['show-on-system-tray']
        self.nothread         = cnf.core['no-thread']
        self.on_close_to_tray = cnf.preferences['on-close-to-tray']

        self.clips = list()
        self.clips_circle = None

        self.view_current = set()

        self.cache = list()
        self.cache_cursor = 0
        self.copy_buffer = ""

        self.pool = ThreadPool(processes=1)

        self.search_engines = list()

        self.makeWidgets()
        self.loadCSS()

        self.engine_default = {
            'name'   : "default",
            'filter' : lambda q: True,
            'piston' : lambda q: { q: self.core.Glossary.search(q.strip().lower()) },
            'cache'  : True,
            'shaft'  : self._view_results,
            'icon'   : None # entry.set_icon_from_icon_name(0, 'utilities-terminal')
        }
        self.searchbar.pop_engine.LAYOUT.add(Gtk.Label('default'))

        self.addEngines_phrase()
        self.addEngines_hashtag()
        self.addEngines_raw()
        self.addEngines_gloss()

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


    def cache_search(self, word):
        for history in self.cache:
            if word not in history.keys(): continue
            print("cache: hit", word, file=fp3)
            return history[word]


    def cache_it(self, results):
        self.cache.append(results)
        self.cache_cursor = len(self.cache) - 1
        self.toolbar.mb_BACKWARD.set_sensitive(True)
        self.toolbar.b_FORWARD.set_sensitive(False)


    def engine_section_search(self, query):
        # TODO: list section also
        # music searches /music/*
        # food searchs en2np/food.tra
        return {}, {}
        cmd = query.split()


    def addEngines_raw(self):
        engine = {
            'name'   : "raw",
            'filter' : lambda q: q[0] == '\\',
            'piston' : lambda q: { q[1:]: self.core.Glossary.search(q[1:]) },
        }

        self.search_engines.append(engine)
        self.searchbar.pop_engine.LAYOUT.add(Gtk.Label(engine['name']))


    def addEngines_hashtag(self):
        engine = {
            'name'   : "hashtag",
            'filter' : lambda q: q[0] == '#',
            'piston' : lambda q: { q: self.core.Glossary.search_hashtag(q) },
        }

        self.search_engines.append(engine)
        self.searchbar.pop_engine.LAYOUT.add(Gtk.Label(engine['name']))


    def addEngines_gloss(self):
        engine = {
            'name'   : "gloss filter",
            'filter' : lambda q: q[0] == '/',
            'piston' : lambda *a: a,
        }

        self.search_engines.append(engine)
        self.searchbar.pop_engine.LAYOUT.add(Gtk.Label(engine['name']))


    def addEngines_phrase(self):
        def _filter(query):
            if not query.find(' '): return False
            if len(query.split(' ')) > 1:
                return True

        # handels cache itself
        def _piston(query):
            results = OrderedDict()
            for q in query.split():
                word = q.lower()
                hit  = self.cache_search(word)
                if hit is not None:
                    results[word] = hit
                    continue
                results[word] = self.core.Glossary.search(word)
            return results

        engine = {
            'name'   : "phrase",
            'filter' : _filter,
            'piston' : _piston,
        }

        self.search_engines.append(engine)
        self.searchbar.pop_engine.LAYOUT.add(Gtk.Label(engine['name']))


    def makeWidgets(self):
        layout = Gtk.Box(orientation=1)
        self.add(layout)

        layout.add(self.makeWidget_toolbar())
        layout.add(self.makeWidget_searchbar())

        vpaned = Gtk.Paned(name="vpaned", orientation=1)
        layout.pack_start(vpaned, expand=1, fill=1, padding=0)

        hpaned = Gtk.Paned(name="hpaned")
        vpaned.pack1(hpaned, resize=0, shrink=0)

        hpaned.pack1(self.makeWidget_sidebar(), resize=0, shrink=0)
        hpaned.pack2(self.makeWidget_viewer(), resize=0, shrink=0)
        hpaned.set_position(164)

        vpaned.pack2(self.makeWidget_relations(), resize=0, shrink=1)
        vpaned.set_position(250)

        layout.show_all()
        layout.add(self.makeWidget_infobar())


    def loadCSS(self):
        # TIP: lets css handeld all fonts related stuff
        self.css_provider = Gtk.CssProvider()
        css = __file__.replace('.py', '.css')
        if not os.path.exists(css): return
        self.css_provider.load_from_path(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


    def makeWidget_toolbar(self):
        self.toolbar = Gtk.Toolbar()

        ## Button Back Button
        self.toolbar.mb_BACKWARD = Gtk.MenuToolButton(icon_name="go-previous")
        self.toolbar.add(self.toolbar.mb_BACKWARD)
        self.toolbar.mb_BACKWARD.connect("clicked", lambda e: self._jump_history(-1))
        self.toolbar.mb_BACKWARD.set_tooltip_markup("Previous, <u>Alt+←</u>")
        self.toolbar.mb_BACKWARD.set_sensitive(False)
        ### History
        self.toolbar.mb_BACKWARD.set_menu(Gtk.Menu())
        self.toolbar.mb_BACKWARD.connect("show-menu", self._show_history)

        ## Button Forward Button
        self.toolbar.b_FORWARD = Gtk.ToolButton(icon_name="go-next")
        self.toolbar.add(self.toolbar.b_FORWARD)
        self.toolbar.b_FORWARD.connect("clicked", lambda e: self._jump_history(+1))
        self.toolbar.b_FORWARD.set_tooltip_markup("Next, <u>Alt+→</u>")
        self.toolbar.b_FORWARD.set_sensitive(False)

        self.toolbar.add(Gtk.SeparatorToolItem())

        ## Smart Copy Toggle Button
        self.toolbar.t_COPY = Gtk.ToggleToolButton(icon_name='edit-copy')
        self.toolbar.add(self.toolbar.t_COPY)
        self.toolbar.t_COPY.set_active(True)

        ## End Separator
        self.toolbar.s_END = Gtk.SeparatorToolItem()
        self.toolbar.add(self.toolbar.s_END)

        return self.toolbar


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
        menu = widget.get_menu()
        print(menu.get_property('visible'))
        l = len(menu.get_children())
        for i, results in enumerate(reversed(self.cache[l:]), l):
            item = Gtk.MenuItem('%d %s'%(i, ', '.join(results)))
            item.show()
            if self.cache_cursor == i:
                item.set_sensitive(False)

            menu.append(item)


    def makeWidget_searchbar(self):
        layout = Gtk.Box()

        label = Gtk.Label(name="searchbar-label")
        layout.add(label)

        # label.set_hexpand(True)
        label.set_markup("<b>Query</b>")

        self.searchbar = _searchbar.Bar()
        layout.add(self.searchbar)

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
        self.searchbar.entry.connect('activate', lambda *a: self.search_and_reflect())

        self.searchbar.set_hexpand(True)
        return layout


    def makeWidget_sidebar(self):
        self.sidebar = _sidebar.Bar()
        treeSelection = self.sidebar.treeview.get_selection()
        self.sidebar.select_signal = treeSelection.connect(
            "changed",
            self.sidebar_on_row_changed
        )

        def _on_key_press(widget, event):
            # NOTE to stop propagation of signal return True
            if event.keyval == 65289: # Tab
                self.searchbar.entry.grab_focus()
                return True

        self.sidebar.connect("key_press_event", _on_key_press)
        return self.sidebar


    def sidebar_on_row_changed(self, treeSelection):
        model, pathlist = treeSelection.get_selected_rows()
        self.clips.clear()
        for path in pathlist:
            self._view_item(*self.sidebar.get_suggestion(path))

        if len(self.clips) == 0: return
        self.clips_circle = circle(self.clips)
        self._circular_search(+1)


    def makeWidget_viewer(self):
        self.viewer = _view.Display(self.PWD)

        def _on_button_press(textview, event):
            if event.type != Gdk.EventType._2BUTTON_PRESS: return
            bounds = self.viewer.textbuffer.get_selection_bounds()
            if not bounds: return
            begin, end = bounds
            query = self.viewer.textbuffer.get_text(begin, end, True)
            self.searchbar.entry.set_text(query)
            self.search_and_reflect(query)

        self.viewer.textview.connect("button-press-event", _on_button_press)
        self.viewer.textview.connect("button-release-event", self.on_button_release)
        self.viewer.b_CLEAR.connect("clicked", self.viewer_clean)

        return self.viewer


    def on_button_release(self, textview, eventbutton):
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


    def viewer_clean(self, widget=None):
        if self.viewer.textbuffer.get_char_count() > 1:
            self.view_current.clear()
            self.viewer.textbuffer.set_text("\n")
            self.copy_buffer = ""
            self.clips_circle = None
            treeSelection = self.sidebar.treeview.get_selection()
            treeSelection.unselect_all()
            return

        self.sidebar.clear()
        self.clips.clear()


    def makeWidget_relations(self):
        self.relatives = _relations.Relatives()
        return self.relatives


    def makeWidget_infobar(self):
        self.infobar = Gtk.InfoBar()

        self.infobar.LABEL = Gtk.Label()
        content = self.infobar.get_content_area()
        content.add(self.infobar.LABEL)

        self.infobar.set_show_close_button(True)
        self.infobar.set_default_response(Gtk.ResponseType.CLOSE)
        self.infobar.connect("response", lambda w, id: w.hide())

        return self.infobar


    def get_active_query(self):
        treeSelection = self.sidebar.treeview.get_selection()
        model, pathlst, = treeSelection.get_selected_rows()

        if pathlst:
            *c, query = model[pathlst[0]]
        else:
            query = self.searchbar.entry.get_text().strip().lower()

        return query


    def do_search_pulse(self, engine, async_ret):
        """Search Pulse Function

        Executing the Gtk.TextViewer in threading crashes. To avoid
        crashing remaining segment which make changes in
        Gtk.TextViewer is moved out of thread and executed after
        results are ready.

        """
        self.searchbar.entry.progress_pulse()
        if not async_ret.ready(): return True
        results = async_ret.get()
        engine.get('shaft', self._view_results)(results)
        if engine.get('cache', False): self.cache_it(results)
        self.searchbar.entry.set_progress_fraction(0)
        return False


    def search_and_reflect(self, query=None, thread=True):
        if query is None:
            query = self.searchbar.entry.get_text()

        if not query: return

        self.searchbar.entry.HISTORY.append(query)
        self.searchbar.entry.CURRENT = len(self.searchbar.entry.HISTORY)

        # choosing engines
        engine = self.engine_default
        for e in self.search_engines:
            if e['filter'](query):
                engine = e
                break

        cache = engine.get('cache', False)
        hit = self.cache_search(query) if cache else None

        if hit:
            engine.get('shaft', self._view_results)({query: hit})
            return

        if self.nothread and thread:
            results = engine['piston'](query)
            engine.get('shaft', self._view_results)(results)
            if cache: self.cache_it(results)
            return

        async_ret = self.pool.apply_async(engine['piston'], (query,))
        timeout_id = GObject.timeout_add(
            400,
            self.do_search_pulse,
            engine,
            async_ret
        )


    def fit_output(self, output):
        if output is None:
            self.infobar.LABEL.set_markup("<b>%s</b> did not gave any output"%query)
            self.infobar.show_all()
            return

        # if its plain string TODO fix it with new engine switcher,
        # which will have output paramenter also
        begin = self.viewer.textbuffer.get_start_iter()
        self.viewer.textbuffer.place_cursor(begin)
        self.viewer.insert_at_cursor("\n")
        if output != '':
            self.viewer.insert_at_cursor(output)
            return

        self.infobar.LABEL.set_markup("<b>%s</b> did not gave any output"%query)
        self.infobar.show_all()


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

        for pos, val in parsed_info.items():
            if   pos == "_t": transliterate += val; continue
            elif pos[0] == "_": continue
            self.clips += val

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


    def insert_plugin_item_on_toolbar(self, widget):
        bar = self.toolbar
        if hasattr(bar, "s_PLUGINS"):
            i = bar.get_item_index(bar.s_PLUGINS)
        else:
            bar.s_PLUGINS = Gtk.SeparatorToolItem()
            i = bar.get_item_index(bar.s_END)
            bar.insert(bar.s_PLUGINS, i)
            bar.s_PLUGINS.show()

        bar.insert(widget, i+1)


    def on_key_press(self, widget, event):
        # NOTE to stop propagation of signal return True
        if  Gdk.ModifierType.CONTROL_MASK & event.state:
            if event.keyval == 65379: # Insert
                if    self.viewer.textbuffer.get_selection_bounds(): self.toolbar.t_COPY.set_active(False)
                elif  self.searchbar.entry.get_selection_bounds()  : self.toolbar.t_COPY.set_active(False)
                else: self._circular_search(+1)
            elif event.keyval == ord('b'): self._circular_search(-1)
            elif event.keyval == ord('B'): self._circular_search(+1)
            elif event.keyval == ord('f'): self._circular_search(+1)
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
    pwd = sys.path[0]+'/../'
    sys.path.append(pwd)
    import setting
    import core
    core.fp3 = core.fp4 = open(os.devnull, 'w')

    cnf = setting.main(pwd)
    core.load_from_config(cnf)

    root = main(core, cnf)
    root.connect('delete-event', Gtk.main_quit)

    # in isolation testing, make Esc quit Gtk mainloop
    root.handle_esc = Gtk.main_quit


if __name__ == '__main__':
    sample()
    Gtk.main()
