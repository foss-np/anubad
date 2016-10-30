#!/usr/bin/env python3

import sys

fp3 = fp4 = sys.stderr

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

class Bar(Gtk.Box):
    def __init__(self):
        Gtk.Box.__init__(self, name="SearchBar")

        style_context = self.get_style_context()
        style_context.add_class(Gtk.STYLE_CLASS_LINKED)
        self.makeWidgets()

        ### Make popovers
        self.pop_reverse = INavHistory(self.entry)
        self.pop_engine = self.makeWidget_popover_engine(self.entry)


    def makeWidgets(self):
        self.set_tooltip_markup("<b>Search:</b> \t⌨ [<i>Enter</i>]")

        ## Entry
        self.entry = Gtk.SearchEntry()
        self.pack_start(self.entry, expand=True, fill=True, padding=0)

        self.entry.set_placeholder_text('type here ...')
        self.entry.set_input_hints(Gtk.InputHints.SPELLCHECK) # TODO: make it work
        self.entry.set_max_length(100)
        self.entry.set_progress_pulse_step(0.4)
        self.entry.set_icon_sensitive(0, True)
        self.entry.set_icon_activatable(0, True)
        self.entry.HISTORY = []
        self.entry.CURRENT = 0

        def _stop_focus_nav(widget, direction):
            # NOTE: avoid losing focus of entry
            if direction == Gtk.DirectionType.UP   : return True
            if direction == Gtk.DirectionType.DOWN : return True

        self.entry.connect('focus', _stop_focus_nav)
        self.entry.connect('key_press_event', self.on_key_press)

        ## Button
        button = Gtk.Button('→')
        self.pack_start(button, expand=False, fill=False, padding=0)
        button.connect('clicked', lambda *a: self.entry.emit('activate'))


    def add_hashtag_completion(self, liststore):
        area = Gtk.CellAreaBox()
        textrender = Gtk.CellRendererText(scale=0.85)
        area.pack_end(textrender, expand=False, align=False, fixed=True)
        area.attribute_connect(textrender, "text", 1)

        self.entrycompletion = Gtk.EntryCompletion.new_with_area(area)
        self.entry.set_completion(self.entrycompletion)

        self.entrycompletion.set_model(liststore)
        self.entrycompletion.set_text_column(0)
        self.entrycompletion.set_inline_selection(True)

        # NOTE just to fix the bug of size
        # self.entrycompletion.insert_action_markup(0, "")
        # self.entrycompletion.delete_action(0)

        def _match_func(entrycompletion, query, treeiter, liststore):
            if not query[0] == '#': return False
            return query[1:] in liststore[treeiter][0]

        self.entrycompletion.set_match_func(_match_func, liststore)


    def makeWidget_popover_engine(self, entry):
        pop = Gtk.Popover.new(entry)
        pop.set_position(Gtk.PositionType.BOTTOM)
        pop.set_border_width(2)
        pop.LAYOUT = Gtk.Box(orientation=1)
        pop.add(pop.LAYOUT)

        pop.LAYOUT.add(Gtk.Label(" engine "))
        return pop


    def show_engine(self, entry, pos, eventbutton):
        if pos != 0: return
        rect = entry.get_icon_area(0)
        self.pop_engine.set_pointing_to(rect)
        self.pop_engine.show_all()


    def nav_history(self, diff):
        length = len(self.entry.HISTORY)
        if length == 0: return True
        i = self.entry.CURRENT + diff
        # print("history_seek:", self.entry.CURRENT, '+', diff, ':', i, '==', length)
        if i >= length: return True
        if i == -1: return True
        self.entry.set_text(self.entry.HISTORY[i])
        self.entry.set_position(-1)
        self.entry.CURRENT = i


    def on_key_press(self, widget, event):
        # NOTE to stop propagation of signal return True
        if   event.keyval == 65362: self.nav_history(-1) # Up-arrow
        elif event.keyval == 65364: self.nav_history(+1) # Down-arrow
        elif Gdk.ModifierType.CONTROL_MASK & event.state:
            if   event.keyval == 65365: self.nav_history(-1) # Pg-Up
            elif event.keyval == 65366: self.nav_history(+1) # Pg-Dn
            elif event.keyval == ord('p'): self.nav_history(-1)
            elif event.keyval == ord('n'): self.nav_history(+1)
            elif event.keyval == ord('s'): self.pop_reverse.show_with_reverse(False)
            elif event.keyval == ord('r'): self.pop_reverse.show_with_reverse(True)
            elif event.keyval == ord('k'): widget.delete_text(widget.get_position(), -1)
            elif event.keyval == ord('e'): widget.set_position(-1)
            elif event.keyval == ord('a'):
                if not widget.get_selection_bounds(): return
                widget.set_position(0)
                return True


class INavHistory(Gtk.Popover):
    def __init__(self, parent):
        Gtk.Popover.__init__(
            self,
            name        = "INav",
            modal       = True,
            relative_to = parent,
        )
        self.parent = parent
        self.nav_position = iter(tuple())

        self.set_border_width(2)
        self.set_position(Gtk.PositionType.BOTTOM)

        self.makeWidgets()
        self.connect("focus", lambda *a: True) # don't loose focus
        self.connect("key_press_event", self.on_key_press)
        self.connect("key_release_event", self.on_key_release)
        self.connect("closed", lambda *a: self.hide())


    def makeWidgets(self):
        layout = Gtk.Box(orientation=0)
        self.add(layout)

        icon = Gtk.Image.new_from_icon_name('document-open-recent', Gtk.IconSize.MENU)
        layout.add(icon)

        self.label = Gtk.Label()
        layout.add(self.label)

        self.entry = Gtk.Entry()
        layout.add(self.entry)
        self.entry.set_has_frame(False)
        self.entry.set_overwrite_mode(True)
        self.entry.connect('changed', self.on_change)
        layout.show_all()
        return layout


    def on_change(self, widget):
        query = widget.get_text()
        if query == "":
            # TODO insert last query before nav search
            self.parent.set_text("")
            return

        def interator():
            for history in reversed(self.parent.HISTORY):
                index = history.find(query)
                if index < 0: continue
                self.parent.set_text(history)
                self.parent.select_region(index, index+len(query))
                yield history

        self.nav_position = interator()
        next(self.nav_position, None)
        self.cache = query


    def on_key_press(self, widget, event):
        if   event.keyval == 65361: self.hide() # left-arrow
        elif event.keyval == 65363: self.hide() # right-arrow
        elif event.keyval == 65293: self.hide() # <enter> return
        elif Gdk.ModifierType.CONTROL_MASK & event.state:
            if   event.keyval == ord('g'): self.hide()
            elif event.keyval == ord('s'): next(self.nav_position, None)
            elif event.keyval == ord('r'): next(self.nav_position, None)


    def on_key_release(self, widget, event):
        if   event.keyval == 65362: self.hide() # Up-arrow
        elif event.keyval == 65364: self.hide() # Down-arrow
        elif event.keyval == 65289: self.hide() # Tab


    def show_with_reverse(self, reverse):
        print("inav: show")
        if reverse: self.label.set_markup(" <b>reverse-i-search:</b> ")
        else: self.label.set_markup(" <b>forward-i-search:</b> ")
        self.show()
        self.entry.grab_focus() # For failsafe


def sample():
    root = Gtk.Window()
    root.connect('delete-event', Gtk.main_quit)
    root.connect( # quit when Esc is pressed
        'key_release_event',
        lambda w, e: Gtk.main_quit() if e.keyval == 65307 else None
    )

    sidebar = Bar()
    sidebar.entry.HISTORY = 'first second third fourth'.split()
    sidebar.entry.CURRENT = 3
    liststore = Gtk.ListStore(str, str)
    liststore.append(["#animal", '9'])
    liststore.append(["#animal.bird", '8'])
    liststore.append(["#animal.reptile", '4'])
    liststore.append(["#animal.reptile.snake", '1'])

    sidebar.add_hashtag_completion(liststore)

    root.add(sidebar)
    root.show_all()
    return root


if __name__ == '__main__':
    sample()
    Gtk.main()
