#!/usr/bin/env python

"""* viewer.py
----------------------------------------------------------------------
A module for the interactive text interface and Decoration.
"""

import os
from gi.repository import Gtk, Pango

class Viewer(Gtk.Overlay):

    def __init__(self, parent=None):
        Gtk.Overlay.__init__(self)
        self.makeWidgets()

    def makeWidgets(self):
        self.scroll = Gtk.ScrolledWindow()
        self.add(self.scroll)
        self.scroll.set_hexpand(True)
        self.scroll.set_vexpand(True)

        #
        ## Setting
        ## TODO: PUT THE LOCK ICON
        self.toggle_edit = Gtk.ToggleToolButton.new_from_stock(Gtk.STOCK_EXECUTE)
        self.add_overlay(self.toggle_edit)
        self.toggle_edit.connect("toggled", self._edit_toggle)
        self.toggle_edit.set_valign(Gtk.Align.START)
        self.toggle_edit.set_halign(Gtk.Align.END)

        self.textview = Gtk.TextView()
        self.scroll.add(self.textview)
        self.textview.set_editable(False)
        self.textview.set_cursor_visible(False)
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD)
        self.textbuffer = self.textview.get_buffer()
        # self.textview.connect("size-allocate", self._autoscroll)

        self.tag_bold = self.textbuffer.create_tag("bold",  weight=Pango.Weight.BOLD)
        self.tag_italic = self.textbuffer.create_tag("italic", style=Pango.Style.ITALIC)
        self.tag_underline = self.textbuffer.create_tag("underline", underline=Pango.Underline.SINGLE)

        self.tag_pos = self.textbuffer.create_tag("pos", foreground="red")
        self.tag_trans = self.textbuffer.create_tag("trans", foreground="blue")
        self.tag_found = self.textbuffer.create_tag("found", background="yellow")


    def _edit_toggle(self, widget):
        state = widget.get_active()
        self.textview.set_editable(state)
        self.textview.set_cursor_visible(state)


    def mark_found(self, text):
        begin = self.textbuffer.get_start_iter()
        end = self.textbuffer.get_end_iter()
        self.textbuffer.remove_tag(self.tag_found, begin, end)

        match = begin.forward_search(text, 0, end)
        if match != None:
            match_start, match_end = match
            self.textbuffer.apply_tag(self.tag_found, match_start, match_end)
            m = self.textbuffer.create_mark("found", match_start)
            self.textview.scroll_mark_onscreen(m)


    def jump_to_end(self):
        end = self.textbuffer.get_end_iter()
        m = self.textbuffer.create_mark("end", end)
        self.textview.scroll_mark_onscreen(m)


    def parse(self, tab, obj, row, _print=True):
        """
        >>> obj = Viewer(root)
        >>> root.add(obj)
        >>> data = [1, 'hello', 'नमस्कार']
        >>> obj.parse(0, None, data)
        0 [1, 'hello', 'नमस्कार']
        ['नमस्कार']
        """
        if os.name is not 'nt': # MSWIN BUG: can't print unicode
            print(tab, row)

        ID, word, raw  = row
        trasliterate = ""
        translations = []
        tags = []
        pos = ""
        level = 0

        fbreak = ftsl = 0
        # TODO: dictonary map of pos-tags
        for i, c in enumerate(raw):
            if c == '[': ftsl = i; level += 1
            elif c == ']':
                trasliterate = raw[ftsl+1:i]
                ftsl = i + 2
                fbreak = i + 2
                level -= 1
            elif c == '(':
                pos = raw[fbreak:i]
                fbreak = i + 1
                level += 1
            elif c == ',':
                if raw[i-1] in ')]': continue
                if level > 0: continue
                translations.append([pos, raw[fbreak:i]])
                fbreak = i+2
            elif c == ')':
                translations.append([pos, raw[fbreak:i]])
                pos = ""
                fbreak = i+3
                level -= 1

        if i - fbreak > 2 or len(translations) < 1:
            translations.append([pos, raw[fbreak:]])

        r = []
        for p, t in translations:
            r += [ u.strip() for u in t.split(',') ]

        if not _print: return r

        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert_with_tags(end, word, self.tag_bold)
        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert_with_tags(end, '    ['+trasliterate+']\n', self.tag_trans)

        for c, t in enumerate(translations):
            end = self.textbuffer.get_end_iter()
            self.textbuffer.insert(end, "%4d. "%(c+1))

            pos_ = t[0].strip() if t[0] else "undefined"
            end = self.textbuffer.get_end_iter()
            self.textbuffer.insert_with_tags(end, pos_, self.tag_pos)

            end = self.textbuffer.get_end_iter()
            self.textbuffer.insert(end, " » ")

            end = self.textbuffer.get_end_iter()
            self.textbuffer.insert(end, t[1].strip()+"\n")

            # print(self.textview.scroll_to_iter(end, 0, True, 1.0, 0.0 ))

        return r


    def _autoscroll(self, *args):
        adj = self.scroll.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())


    def not_found(self, word):
        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert_with_tags(end, "'%s'"%word, self.tag_bold)

        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert(end, " Not Found\n")

        self.jump_to_end()


def root_binds(widget, event):
    # print(event.keyval)
    if event.keyval == 65307:
        Gtk.main_quit()


def main():
    global root
    root = Gtk.Window()
    root.connect('delete-event', Gtk.main_quit)
    root.connect('key_release_event', root_binds)
    root.set_default_size(500, 300)


if __name__ == '__main__':
    main()
    import doctest
    doctest.testmod()
    root.show_all()
    Gtk.main()
