#!/usr/bin/env python3

import sys

fp3 = fp4 = sys.stderr

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

class Bar(Gtk.HBox):
    def __init__(self):
        Gtk.HBox.__init__(self)
        self.track_FONT = set()
        self.makeWidgets()


    def makeWidgets(self):
        ## Label
        label = Gtk.Label()
        label.set_markup("<b>Query</b>")
        self.pack_start(label, expand=False, fill=False, padding=60)

        tool_tip = "<b>Search:</b> \t⌨ [<i>Enter</i>]"
        self.pack_start(self.makeWidget_entry(), expand=True, fill=True, padding=2)
        self.entry.connect('key_press_event', self.on_key_press)

        ## Search Button
        # self.b_search = Gtk.Button.new_with_mnemonic('_Search')
        self.b_search = Gtk.Button.new_from_icon_name("pan-down-symbolic", Gtk.IconSize.BUTTON)
        self.b_search.set_label('_Search')
        self.b_search.set_use_underline(True)
        self.pack_start(self.b_search, expand=False, fill=False, padding=1)
        self.b_search.connect('clicked', lambda w: _on_key_release(w, None))

        self.entry.set_tooltip_markup(tool_tip)
        self.b_search.set_tooltip_markup(tool_tip)


    def makeWidget_entry(self):
        self.entry = Gtk.SearchEntry()

        self.entry.set_placeholder_text('type here ...')
        self.entry.set_max_length(32)
        self.entry.set_progress_pulse_step(0.4)
        self.entry.HISTORY = []
        self.entry.CURRENT = 0
        return self.entry


    def add_hashtag_completion(self, liststore):
        self.entrycompletion = Gtk.EntryCompletion()
        self.entry.set_completion(self.entrycompletion)

        self.entrycompletion.set_model(liststore)
        self.entrycompletion.set_text_column(0)

        # NOTE just to fix the bug of size
        # self.entrycompletion.insert_action_markup(0, "")
        # self.entrycompletion.delete_action(0)

        def _match_func(entrycompletion, query, treeiter, liststore):
            if not query[0] == '#': return False
            return query[1:] in liststore[treeiter][0]

        self.entrycompletion.set_match_func(_match_func, liststore)


    def on_key_press(self, widget, event):
        # NOTE to stop propagation of signal return True
        if   event.keyval == 65362: return self.entry_nav_history(-1) # Up-arrow
        elif event.keyval == 65364: return self.entry_nav_history(+1) # Down-arrow
        elif Gdk.ModifierType.CONTROL_MASK & event.state:
            if   event.keyval == 65365: return self.search_entry_nav_history(-1) # Pg-Up
            elif event.keyval == 65366: return self.search_entry_nav_history(+1) # Pg-Dn
            elif event.keyval == ord('p'): return self.search_entry_nav_history(-1)
            elif event.keyval == ord('n'): return self.search_entry_nav_history(+1)
            elif event.keyval == ord('k'): widget.delete_text(widget.get_position(), -1)
            elif event.keyval == ord('e'): widget.set_position(-1)
            elif event.keyval == ord('a'):
                if not widget.get_selection_bounds(): return
                widget.set_position(0)
                return True


    def entry_nav_history(self, diff):
        length = len(self.entry.HISTORY)
        if length == 0: return True
        i = self.entry.CURRENT + diff
        # print("history_seek:", self.search_entry.CURRENT, '+', diff, ':', i, '==', length)
        if i >= length: return True
        if i == -1: return True
        self.entry.set_text(self.entry.HISTORY[i])
        self.entry.set_position(-1)
        self.entry.CURRENT = i
        return True


def sample():
    root = Gtk.Window()
    root.connect('delete-event', Gtk.main_quit)
    root.connect( # quit when Esc is pressed
        'key_release_event',
        lambda w, e: Gtk.main_quit() if e.keyval == 65307 else None
    )
    root.set_default_size(300, 200)

    sidebar = Bar(root)
    root.add(sidebar)
    root.show_all()
    return root


if __name__ == '__main__':
    sample()
    Gtk.main()
