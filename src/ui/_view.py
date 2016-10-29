#!/usr/bin/env python3

"""* viewer.py
----------------------------------------------------------------------
A module for the interactive text interface and Decoration.
"""

POS_MAP = {
    'n'    : "noun",
    'j'    : "adjective",
    'adj'  : "adjective",
    'adv'  : "adverb",
    'v'    : "verb",
    'm'    : "meaning",
}

import os
from subprocess import Popen

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Pango
from gi.repository import GdkPixbuf

# NOTE: Gtk.Overlay is used instead Gtk.TextView.add_child_in_window()
# doesn't move while expanding.
class Display(Gtk.Overlay):
    # hand_cursor = Gdk.Cursor(Gdk.CursorType.HAND2)
    # regular_cursor = Gdk.Cursor(Gdk.CursorType.XTERM)

    def __init__(self, pwd=""):
        Gtk.Overlay.__init__(self, name="Display")
        self.PWD = pwd
        self.pixbuf_cache = dict()

        self.makeWidgets()

        # self.textview.connect("motion-notify-event", self._on_hover)
        # self.textview.connect("event-after", self.event_after)
        # self.textview.connect("visibility-notify-event", self.visibility_notify_event)
        # self.textview.connect('enter-notify-event', self._enter)
        # self.textview.connect('leave-notify-event', self._leave)


    def makeWidgets(self):
        self.add(self.makeWidget_textview())

        self.b_CLEAR = Gtk.ToolButton(
            name      = 'overlay-widget',
            icon_name = 'gtk-clear'
        )
        self.add_overlay(self.b_CLEAR)
        self.b_CLEAR.set_valign(Gtk.Align.START)
        self.b_CLEAR.set_halign(Gtk.Align.END)

        # self.pack_start(self.makeWidget_toolbar(), expand=0, fill=1, padding=0)

        buffer = self.textview.get_buffer()
        self.textbuffer = buffer

        self.tag_li      = buffer.create_tag("li", foreground="gray", weight=Pango.Weight.BOLD)
        self.tag_pos     = buffer.create_tag("pos", foreground="red")
        self.tag_bold    = buffer.create_tag("bold", weight=Pango.Weight.BOLD)
        self.tag_trans   = buffer.create_tag("trans", foreground="blue")
        self.tag_found   = buffer.create_tag("found", background="yellow")
        self.tag_source  = buffer.create_tag("source", foreground="gray", scale=.65)
        self.tag_example = buffer.create_tag("example", foreground="blue", style=Pango.Style.ITALIC)
        self.tag_unicode = buffer.create_tag("unicode", scale=1.2)
        self.tag_hashtag = buffer.create_tag("hashtag", foreground="blue", weight=Pango.Weight.BOLD, scale=.85)


    def makeWidget_textview(self):
        scroll = Gtk.ScrolledWindow()
        scroll.set_hexpand(True)
        scroll.set_vexpand(True)

        self.textview = Gtk.TextView()
        scroll.add(self.textview)

        self.textview.set_editable(False)
        self.textview.set_cursor_visible(False)
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD)

        self.textview.set_left_margin(10)
        self.textview.set_right_margin(20)
        # NOTE: vvv problem with old gtk
        self.textview.set_top_margin(-15) # hack for next search separation '\n'

        return scroll





    def jump_to(self, textIter):
        mark = self.textbuffer.create_mark(None, textIter)
        self.textview.scroll_mark_onscreen(mark)
        self.textbuffer.delete_mark(mark)


    def jump_to_top(self):
        self.jump_to(self.textbuffer.get_start_iter())


    def jump_to_bottom(self):
        self.jump_to(self.textbuffer.get_end_iter())


    def insert_at_cursor(self, text, tag=None):
        if tag == None:
            self.textbuffer.insert_at_cursor(text)
            return

        mark = self.textbuffer.get_insert()
        end =  self.textbuffer.get_iter_at_mark(mark)
        self.textbuffer.insert_with_tags(end, text, tag)


    def clean_highlights(self):
        begin = self.textbuffer.get_start_iter()
        end = self.textbuffer.get_end_iter()
        self.textbuffer.remove_tag(self.tag_found, begin, end)
        return begin, end


    def find_and_highlight(self, text, point, n=1, reverse=False):
        """
        n - number of match to repeat
        n < 0 - match all
        """
        if reverse: match = point.backward_search(text, 0)
        else:       match = point.forward_search(text, 0)

        if match == None: return
        match_start, match_stop = match

        self.textbuffer.apply_tag(self.tag_found, match_start, match_stop)

        if n <= 1: return match

        if reverse: self.find_and_highlight(text, match_start, n - 1, reverse)
        else:       self.find_and_highlight(text, match_stop, n - 1)

        return match


    def get_wordObj_at_cursor(self):
        mark = self.textbuffer.get_insert()
        end  = self.textbuffer.get_iter_at_mark(mark)
        char = end.get_char()

        if not end.forward_word_end(): return
        begin = end.copy()
        if not begin.backward_word_start(): return
        word = self.textbuffer.get_text(begin, end, True)

        ## validate the word
        if char not in word: return
        return word, begin, end


    def _on_hover(self, textview, event):
        # broken due to Gtk 3.0
        hovering = False
        x, y = textview.window_to_buffer_coords(Gtk.TextWindowType.WIDGET, int(event.x), int(event.y))
        point = textview.get_iter_at_location(x, y)

        for tag in point.get_tags():
            if tag.get_property('name') in ['source']:
                hovering = True
                break

        cursor = self.hand_cursor if hovering else self.regular_cursor

        window = textview.get_window(Gtk.TextWindowType.WIDGET)
        window.set_cursor(cursor)


    def insert_result(self, word, parsed_info, src='\n'):
        """
        >>> obj = root.get_children()[0]
        >>> obj.insert_result('hello', [('unknown', 'नमस्कार')], 'gloss/demo')
        >>> obj.insert_result('hello',\
        [('_transliterate', 'हेल्\u200dलो'),\
        ('noun', 'नमस्कार'), ('noun', 'नमस्ते'),\
        ('unknown', ''), ('verb', 'स्वागत'), ('verb', 'अभिवादन'), ('verb', 'सम्बोधन'), ('verb', 'जदौ')],\
        'gloss/demo')
        >>> obj.insert_result('rhythm',\
        [('noun', 'ताल'), ('unknown', ''), ('_#', '#music'), ('noun', 'लय'), ('_transliterate', 'रिदम')],\
        'gloss/demo')
        >>> obj.insert_result('treble',\
        [('unknown', 'G clef'), ('_unicode', '0x1D11E'), ('unknown', ''), ('_#', '#clef')],\
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
        self.insert_at_cursor(word, self.tag_bold)

        info = iter(parsed_info)
        pos, val = next(info)
        if pos != "_transliterate": info = parsed_info
        else: self.insert_at_cursor('  [%s]'%val, self.tag_trans)

        if src != '\n':
            *a, tmp = src.split('gloss/')
            # tag = self.textbuffer.create_tag(None, foreground="gray", scale=.65)
            # tag.set_data("src", src)
            self.insert_at_cursor("\n")
            self.insert_at_cursor("source: "+tmp, self.tag_source)

        _pos = ""
        c = 0
        note = ""
        pre = ""
        for pos, val in info:
            if pos == "_transliterate":
                self.insert_at_cursor('  [%s]'%val, self.tag_trans)
                continue

            if pos == "_#":
                self.insert_at_cursor(' '+val, self.tag_hashtag)
                continue

            if pos == "_unicode":
                c += 1
                self.insert_at_cursor("\n%4d. "%c, self.tag_li)
                self.insert_at_cursor("unicode", self.tag_pos)
                self.insert_at_cursor(" » ")
                self.insert_at_cursor(val + " → ")
                self.insert_at_cursor("%4s"%chr(int(val, 16)), self.tag_unicode)
                continue
            if pos == "_note": pre = "<%s>"%val; continue
            if pos == "_wiki": self.link_wiki(val); continue
            if val == "": _pos = ""; continue
            if pos == "_sci": pos = "scientific name"
            if pos != _pos:
                c += 1
                self.insert_at_cursor("\n%4d. "%c, self.tag_li)
                self.insert_at_cursor(
                    ':'.join(POS_MAP.get(p, p) for p in pos.split(':')),
                    self.tag_pos
                )
                self.insert_at_cursor(" » ")
            else:
                self.insert_at_cursor(", ")

            if pre != "":
                self.insert_at_cursor(pre)
                pre = ""

            self.insert_at_cursor(val)
            _pos = pos
        else:
            self.insert_at_cursor("\n")


    def not_found(self, text, msg=""):
        self.insert_at_cursor(text, self.tag_bold)
        self.insert_at_cursor(" Not Found %s\n"%msg)
        self.jump_to_top()


    def link_wiki(self, key):
        self.insert_at_cursor(" ")

        def url_clicked(textag, textview, event, textiter):
            if event.type != Gdk.EventType.BUTTON_RELEASE: return #and event.button == 1:
            cmd = [
                'setsid',
                self.cnf.apps['browser'],
                "https://en.wikipedia.org/wiki/%s"%key
            ]
            print("pid:", Popen(cmd).pid)
            # webbrowser.open("https://en.wikipedia.org/wiki/"+key)

        tag = self.textbuffer.create_tag(None)
        tag.connect("event", url_clicked )
        # tag.connect("enter-notify-event", self._enter)

        ## get start offset
        mark  = self.textbuffer.get_insert()
        start = self.textbuffer.get_iter_at_mark(mark)
        start_offset = start.get_offset()
        # print(offset)

        self.insert_image(start, self.PWD + '../assets/wiki.svg')

        ## get stop offset
        start = self.textbuffer.get_iter_at_offset(start_offset)
        mark  = self.textbuffer.get_insert()
        stop  = self.textbuffer.get_iter_at_mark(mark)

        self.textbuffer.apply_tag(tag, start, stop)


    def insert_image(self, textIter, path, size=16):
        # TODO: fall back if image does'nt exist
        if path not in self.pixbuf_cache:
            if os.path.exists(path):
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(path, size, size)
            else:
                print(path, "icon not found")
                return

            self.pixbuf_cache[path] = pixbuf

        self.textbuffer.insert_pixbuf(textIter, self.pixbuf_cache[path])


    # def insert_link(self, text, href):
    #     tag = self.textbuffer.create_tag(None, foreground="blue", underline=Pango.UNDERLINE_SINGLE)
    #     tag.set_data("href", href)
    #     self.insert_at_cursor(text, href)


    # def url_clicked(self, textag, textview, event, textiter):
    #     if event.type == Gdk.EventType.BUTTON_RELEASE: #and event.button == 1:
    #         print("pid:", Popen(['setsid', BROWSER, "https://en.wikipedia.org/wiki/%s"%key]).pid)
    #         # webbrowser.open("https://en.wikipedia.org/wiki/"+key)


    # def link_button(self):
    #     link = Gtk.LinkButton(uri="https://en.wikipedia.org/wiki/", label="wiki")
    #     link.show()
    #     # link.set_size_request(30, 40)
    #     anchor = Gtk.TextChildAnchor()
    #     end = self.textbuffer.get_end_iter()
    #     self.textbuffer.insert_child_anchor(end, anchor)
    #     self.textview.add_child_at_anchor(link, anchor)


def sample():
    filepath = os.path.abspath(__file__)
    PWD = os.path.dirname(filepath) + '/../'

    root = Gtk.Window()
    root.connect('delete-event', Gtk.main_quit)
    root.connect( # quit when Esc is pressed
        'key_release_event',
        lambda w, e: Gtk.main_quit() if e.keyval == 65307 else None
    )
    root.set_default_size(500, 300)

    obj = Display(PWD)
    obj.textbuffer.set_text("\n")
    obj.b_CLEAR.connect("clicked", lambda *a: obj.textbuffer.set_text(""))
    root.add(obj)
    root.show_all()
    return root


if __name__ == '__main__':
    root = sample()

    import doctest
    doctest.testmod()

    Gtk.main()
