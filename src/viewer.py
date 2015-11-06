#!/usr/bin/env python3

"""* viewer.py
----------------------------------------------------------------------
A module for the interactive text interface and Decoration.
"""

import os
import webbrowser
from gi.repository import Gtk, Gdk, Pango

class Viewer(Gtk.Overlay):
    """
    Viewer is charged Gtk.TextView
    # TODO: Viewer object access TextView members
    """

    def __init__(self, parent=None):
        Gtk.Overlay.__init__(self)
        self._parent = parent # overlay has the parent field
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
        self.tb_clean.connect("clicked", lambda *a: self.clean())
        self.tb_clean.set_valign(Gtk.Align.START)
        self.tb_clean.set_halign(Gtk.Align.END)

        self.textview = Gtk.TextView()
        self.scroll.add(self.textview)
        self.textview.set_editable(False)
        self.textview.set_cursor_visible(False)
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD)
        self.textview.set_left_margin(10)
        self.textview.set_right_margin(20)

        buffer = self.textview.get_buffer()
        self.textbuffer = buffer

        self.tag_bold = buffer.create_tag("bold",  weight=Pango.Weight.BOLD)
        # self.tag_italic = buffer.create_tag("italic", style=Pango.Style.ITALIC)
        # self.tag_underline = buffer.create_tag("underline", underline=Pango.Underline.SINGLE)

        self.tag_li = buffer.create_tag("li", foreground="gray", weight=Pango.Weight.BOLD)
        self.tag_pos = buffer.create_tag("pos", foreground="red")
        self.tag_trans = buffer.create_tag("trans", foreground="blue")
        self.tag_example = buffer.create_tag("example", foreground="blue", style=Pango.Style.ITALIC)
        self.tag_source = buffer.create_tag("source", foreground="gray", scale=.65)
        self.tag_found = buffer.create_tag("found", background="yellow")
        self.tag_hashtag = buffer.create_tag("hashtag", foreground="blue", weight=Pango.Weight.BOLD)

        # self.tag_url = buffer.create_tag("url", foreground="blue", underline=Pango.Underline.SINGLE)
        # self.tag_url.connect("event", self._url_clicked)


    def clean(self):
        # NOTE: kept outside because it needs wrapping
        self.textbuffer.set_text("")


    def mark_found(self, text, begin, n=1):
        """
        n - number of match to repeat
        n < 0 - match all
        """
        end = self.textbuffer.get_end_iter()
        match = begin.forward_search(text, 0, end)
        if match != None:
            match_start, match_end = match
            self.textbuffer.apply_tag(self.tag_found, match_start, match_end)
            if n > 1:
                self.mark_found(text, match_end, n - 1)
            return match_start
        return None


    def jump_to_end(self):
        end = self.textbuffer.get_end_iter()
        m = self.textbuffer.create_mark("end", end)
        self.textview.scroll_mark_onscreen(m)


    def parse(self, data, src='\n', print_=True):
        """
        >>> obj.parse([1, 'hello', 'नमस्कार'])
        1 hello नमस्कार
        """

        ID, word, raw = data

        if os.name is not 'nt': # MSWIN BUG: can't print unicode
            print(ID, word, raw)

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
                fbreak = i + 2
            elif c == ')':
                translations.append([pos, raw[fbreak:i]])
                pos = ""
                fbreak = i + 3
                level -= 1

        if i - fbreak > 2 or len(translations) < 1:
            translations.append([pos, raw[fbreak:]])

        r = []
        for p, t in translations:
            r += [ u.strip() for u in t.split(',') ]

        # NOTE: _parent because overlay has its own too
        self._parent.clips += r
        if not print_: return

        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert_with_tags(end, word, self.tag_bold)
        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert_with_tags(end, '    ['+trasliterate+']', self.tag_trans)

        if src != '\n':
            *a, gloss, lang, label = src.split('/')
            src = " source: %s/%s/%s\n"%(gloss, lang, label)

        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert_with_tags(end, src, self.tag_source)

        for c, t in enumerate(translations):
            end = self.textbuffer.get_end_iter()
            self.textbuffer.insert_with_tags(end, "%4d. "%(c+1), self.tag_li)

            pos_ = t[0].strip() if t[0] else "undefined"
            end = self.textbuffer.get_end_iter()
            self.textbuffer.insert_with_tags(end, pos_, self.tag_pos)

            end = self.textbuffer.get_end_iter()
            self.textbuffer.insert(end, " » ")

            end = self.textbuffer.get_end_iter()
            self.textbuffer.insert(end, t[1].strip()+"\n")


    def append_result(self, word, parsed_info, src='\n'):
        """
        >>> obj.append_result('hello', [('unknown', 'नमस्कार')], 'gloss/demo')
        >>> obj.append_result('hello',\
        [('transliterate', 'हेल्\u200dलो'),\
        ('noun', 'नमस्कार'), ('noun', 'नमस्ते'),\
        ('unknown', ''), ('verb', 'स्वागत'), ('verb', 'अभिवादन'), ('verb', 'सम्बोधन'), ('verb', 'जदौ')],\
        'gloss/demo')
        >>> obj.append_result('wheat',\
        [('transliterate', 'वीट्'),\
        ('noun', 'गहूँ'),\
        ('#', 'crop'),\
        ('#', 'food'),\
        ('wiki', 'Wheat')],\
        'gloss/demo')
        """
        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert_with_tags(end, word, self.tag_bold)

        info = iter(parsed_info)
        pos, val = next(info)
        if pos == "transliterate":
            end = self.textbuffer.get_end_iter()
            self.textbuffer.insert_with_tags(end, '  [%s]'%val, self.tag_trans)
        else:
            info = parsed_info

        if src != '\n':
            *a, tmp = src.split('gloss/')
            end = self.textbuffer.get_end_iter()
            self.textbuffer.insert_with_tags(end, "\nsource: %s"%tmp, self.tag_source)

        _pos = ""
        c = 0
        for pos, val in info:
            if pos == "transliterate":
                end = self.textbuffer.get_end_iter()
                self.textbuffer.insert_with_tags(end, '  [%s]'%val, self.tag_trans)
                continue;
            if pos == "#":
                end = self.textbuffer.get_end_iter()
                self.textbuffer.insert(end, "  ")
                end = self.textbuffer.get_end_iter()
                self.textbuffer.insert_with_tags(end, "#"+val, self.tag_hashtag)
                continue
            if pos == "wiki": self.link_wiki(val); continue
            if val == "": _pos = ""; continue
            if pos != _pos:
                c += 1
                end = self.textbuffer.get_end_iter()
                self.textbuffer.insert_with_tags(end, "\n%4d. "%c, self.tag_li)

                end = self.textbuffer.get_end_iter()
                self.textbuffer.insert_with_tags(end, pos, self.tag_pos)

                end = self.textbuffer.get_end_iter()
                self.textbuffer.insert(end, " » ")
            else:
                end = self.textbuffer.get_end_iter()
                self.textbuffer.insert(end, ", ")

            end = self.textbuffer.get_end_iter()
            self.textbuffer.insert(end, val)
            self._parent.clips.append(val)
            _pos = pos
        else:
            end = self.textbuffer.get_end_iter()
            self.textbuffer.insert(end, "\n")



    def _autoscroll(self, *args):
        adj = self.scroll.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())


    def not_found(self, word, msg=""):
        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert_with_tags(end, "'%s'"%word, self.tag_bold)

        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert(end, " Not Found %s\n"%msg)


    # def _leave(self, *args):
    #     self.parent.set_cursor(None)

    # def _enter(self, *args):
    #     self.parent.set_cursor(Gdk.Cursor(Gdk.HAND2))

    def link_wiki(self, key):
        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert(end, " ")

        def url_clicked(textag, textview, event, textiter):
            if event.type == Gdk.EventType.BUTTON_RELEASE: #and event.button == 1:
                webbrowser.open("https://en.wikipedia.org/wiki/"+key)

        tag = self.textbuffer.create_tag(None, foreground="blue", underline=Pango.Underline.SINGLE)
        tag.connect("event", url_clicked )
        # tag.connect("enter-notify-event", self._enter)

        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert_with_tags(end, "wiki", tag)


    def link_button(self):
        link = Gtk.LinkButton(uri="https://en.wikipedia.org/wiki/", label="wiki")
        link.show()
        # link.set_size_request(30, 40)
        anchor = Gtk.TextChildAnchor()
        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert_child_anchor(end, anchor)
        self.textview.add_child_at_anchor(link, anchor)


    def add_anchor(self):
        end = self.viewer.textbuffer.get_end_iter()
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(PWD + 'globe.svg')
        self.viewer.textbuffer.insert_pixbuf(end, pixbuf)


    def add_pic(self):
        pixbuf = GdkPixbuf('')
        pixbuf.scale_simple(dest_width, dest_height, gtk.gdk.INTERP_BILINEAR)
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
    root.clips = []

    global obj
    obj = Viewer(root)
    root.add(obj)
    return root


if __name__ == '__main__':
    root = main()
    import doctest
    doctest.testmod()
    root.show_all()
    Gtk.main()
