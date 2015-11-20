#!/usr/bin/env python3

"""* viewer.py
----------------------------------------------------------------------
A module for the interactive text interface and Decoration.
"""

import os
from subprocess import Popen

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Pango
from gi.repository import GdkPixbuf

class Display(Gtk.Overlay):
    """
    Display is charged Gtk.TextView
    # TODO: Viewer object access TextView members
    """

    def __init__(self, parent=None):
        Gtk.Overlay.__init__(self)
        self._parent = parent # overlay has the parent field
        self.pixbuf_cache = dict()

        self.makeWidgets()

        self.set_hexpand(True)
        self.set_vexpand(True)

        # self.textview.connect('enter-notify-event', self._enter)
        # self.textview.connect('leave-notify-event', self._leave)


    def makeWidgets(self):
        self.scroll = Gtk.ScrolledWindow()
        self.add(self.scroll)
        self.scroll.set_hexpand(True)
        self.scroll.set_vexpand(True)

        self.tb_clean = Gtk.ToolButton(icon_name=Gtk.STOCK_CLEAR)
        self.add_overlay(self.tb_clean)

        self.tb_clean.set_valign(Gtk.Align.START)
        self.tb_clean.set_halign(Gtk.Align.END)

        self.textview = Gtk.TextView()
        self.scroll.add(self.textview)
        self.textview.set_editable(False)
        self.textview.set_cursor_visible(False)
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD)
        self.textview.set_top_margin(-15) # hack for next search separation '\n'
        self.textview.set_left_margin(10)
        self.textview.set_right_margin(20)

        buffer = self.textview.get_buffer()
        self.textbuffer = buffer

        self.tag_bold = buffer.create_tag("bold", weight=Pango.Weight.BOLD)
        self.tag_li = buffer.create_tag("li", foreground="gray", weight=Pango.Weight.BOLD)
        self.tag_pos = buffer.create_tag("pos", foreground="red")
        self.tag_trans = buffer.create_tag("trans", foreground="blue")
        self.tag_example = buffer.create_tag("example", foreground="blue", style=Pango.Style.ITALIC)
        self.tag_source = buffer.create_tag("source", foreground="gray", scale=.65)
        self.tag_found = buffer.create_tag("found", background="yellow")
        self.tag_hashtag = buffer.create_tag("hashtag", foreground="blue", weight=Pango.Weight.BOLD)


    def find_and_highlight(self, text, point, n=1, reverse=False):
        """
        n - number of match to repeat
        n < 0 - match all
        """
        if reverse: match = point.backward_search(text, 0)
        else:       match = point.forward_search(text, 0)

        if match != None:
            match_start, match_end = match
            self.textbuffer.apply_tag(self.tag_found, match_start, match_end)
            if n > 1:
                self.find_and_highlight(text, match_end, n - 1)
            return match_start
        return None


    def jump_to(self, textIter):
        mark = self.textbuffer.create_mark(None, textIter)
        self.textview.scroll_mark_onscreen(mark)
        self.textbuffer.delete_mark(mark)


    def jump_to_top(self):
        self.jump_to(self.textbuffer.get_start_iter())


    def jump_to_bottom(self):
        self.jump_to(self.textbuffer.get_end_iter())


    def get_cursor_textIter(self):
        mark = self.textbuffer.get_mark('insert')
        return self.textbuffer.get_iter_at_mark(mark)


    def insert_result(self, word, parsed_info, src='\n'):
        """
        >>> obj.insert_result('hello', [('unknown', 'नमस्कार')], 'gloss/demo')
        >>> obj.insert_result('hello',\
        [('_transliterate', 'हेल्\u200dलो'),\
        ('noun', 'नमस्कार'), ('noun', 'नमस्ते'),\
        ('unknown', ''), ('verb', 'स्वागत'), ('verb', 'अभिवादन'), ('verb', 'सम्बोधन'), ('verb', 'जदौ')],\
        'gloss/demo')
        >>> obj.insert_result('wheat',\
        [('_transliterate', 'वीट्'),\
        ('noun', 'गहूँ'),\
        ('_#', 'crop'), ('_#', 'food'),\
        ('_wiki', 'Wheat')],\
        'gloss/demo')
        >>> obj.insert_result('black mustard',\
        [('_note', 'plant'), ('note', 'तोरी'), ('_#', 'spice'), ('noun', ''),\
        ('_note', 'leaves'), ('noun', 'तोरीको साग'), ('_#', 'vegetable'),\
        ('_sci', 'Brassica nigra L')],\
        'gloss/demo')
        >>> obj.insert_result('creation',\
        [('unknown', 'सृजना'), ('_note', 'कीर्ति')],\
        'gloss/demo')
        """
        end = self.get_cursor_textIter()
        self.textbuffer.insert_with_tags(end, word, self.tag_bold)

        info = iter(parsed_info)
        pos, val = next(info)
        if pos == "_transliterate":
            end = self.get_cursor_textIter()
            self.textbuffer.insert_with_tags(end, '  [%s]'%val, self.tag_trans)
        else:
            info = parsed_info

        if src != '\n':
            *a, tmp = src.split('gloss/')
            end = self.get_cursor_textIter()
            self.textbuffer.insert_with_tags(end, "\nsource: "+tmp, self.tag_source)

        _pos = ""
        c = 0
        note = ""
        pre = ""
        for pos, val in info:
            if pos == "_transliterate":
                end = self.get_cursor_textIter()
                self.textbuffer.insert_with_tags(end, '  [%s]'%val, self.tag_trans)
                continue;
            if pos == "_#":
                self.textbuffer.insert_at_cursor(' ')
                end = self.get_cursor_textIter()
                self.textbuffer.insert_with_tags(end, "#"+val, self.tag_hashtag)
                continue
            if pos == "_note": pre = "<%s>"%val; continue
            if pos == "_wiki": self.link_wiki(val); continue
            if val == "": _pos = ""; continue
            if pos == "_sci": pos = "scientific name"
            if pos != _pos:
                c += 1
                end = self.get_cursor_textIter()
                self.textbuffer.insert_with_tags(end, "\n%4d. "%c, self.tag_li)

                end = self.get_cursor_textIter()
                self.textbuffer.insert_with_tags(end, pos, self.tag_pos)
                self.textbuffer.insert_at_cursor(" » ")
            else:
                self.textbuffer.insert_at_cursor(", ")

            if pre != "":
                self.textbuffer.insert_at_cursor(pre)
                pre = ""

            self.textbuffer.insert_at_cursor(val)
            _pos = pos
        else:
            self.textbuffer.insert_at_cursor("\n")


    def _autoscroll(self, *args):
        adj = self.scroll.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())


    def not_found(self, word, msg=""):
        end = self.get_cursor_textIter()
        self.textbuffer.insert_with_tags(end, "%s"%word, self.tag_bold)
        self.textbuffer.insert_at_cursor(" Not Found %s\n"%msg)
        self.jump_to_top()


    # def _leave(self, *args):
    #     self.parent.set_cursor(None)


    # def _enter(self, *args):
    #     self.parent.set_cursor(Gdk.Cursor(Gdk.HAND2))


    def link_wiki(self, key):
        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert(end, " ")

        def url_clicked(textag, textview, event, textiter):
            if event.type == Gdk.EventType.BUTTON_RELEASE: #and event.button == 1:
                print("pid:", Popen(['setsid', BROWSER, "https://en.wikipedia.org/wiki/%s"%key]).pid)
                # webbrowser.open("https://en.wikipedia.org/wiki/"+key)

        tag = self.textbuffer.create_tag(None)
        tag.connect("event", url_clicked )
        # tag.connect("enter-notify-event", self._enter)

        end = self.textbuffer.get_end_iter()
        offset = end.get_offset()
        # print(offset)
        self.insert_image('../assets/globe.svg')
        end = self.textbuffer.get_end_iter()
        begin = self.textbuffer.get_iter_at_offset(offset)
        self.textbuffer.apply_tag(tag, begin, end)
        # self.textbuffer.insert_with_tags(end, "wiki", tag)


    def link_button(self):
        link = Gtk.LinkButton(uri="https://en.wikipedia.org/wiki/", label="wiki")
        link.show()
        # link.set_size_request(30, 40)
        anchor = Gtk.TextChildAnchor()
        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert_child_anchor(end, anchor)
        self.textview.add_child_at_anchor(link, anchor)


    def insert_image(self, file):
        end = self.textbuffer.get_end_iter()
        if file in self.pixbuf_cache:
            self.textbuffer.insert_pixbuf(end, self.pixbuf_cache[file])
            return

        pixbuf = GdkPixbuf.Pixbuf.new_from_file(PWD + file)
        new = pixbuf.scale_simple(16, 16, GdkPixbuf.InterpType.BILINEAR)
        self.pixbuf_cache[file] = new
        self.textbuffer.insert_pixbuf(end, new)


    def add_pic(self):
        pixbuf = GdkPixbuf('')
        self.viewer.insert_pixbuf()


def root_binds(widget, event):
    # print(event.keyval)
    if event.keyval == 65307:
        Gtk.main_quit()


def main():
    root = Gtk.Window()
    root.connect('delete-event', Gtk.main_quit)
    root.connect('key_release_event', root_binds)
    root.set_default_size(500, 300)

    global obj
    obj = Display(root)
    obj.textbuffer.insert_at_cursor("\n")
    obj.tb_clean.connect("clicked", lambda *a: obj.textbuffer.set_text(""))
    root.add(obj)
    return root


if __name__ == '__main__':
    __filepath__ = os.path.abspath(__file__)
    PWD = os.path.dirname(__filepath__) + '/'

    root = main()

    import doctest
    doctest.testmod()
    root.show_all()
    Gtk.main()
