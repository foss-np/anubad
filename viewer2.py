#!/usr/bin/env python

if __name__ == '__main__':
    exec(open("mysettings.conf").read())
    exec(open("gsettings.conf").read())
    import sys
    sys.path.append(PATH_MYLIB)
    from debugly import *

from gi.repository import Gtk, Pango

class Viewer(Gtk.ScrolledWindow):
    def __init__(self, parent=None):
        Gtk.ScrolledWindow.__init__(self)
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.makeWidgets()
        self.bindWidgets()

    def makeWidgets(self):
        self.textview = Gtk.TextView()
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD)
        self.textbuffer = self.textview.get_buffer()
        self.add_with_viewport(self.textview)
        self.textview.connect("size-allocate", self._autoscroll)
        # self.add(self.textview)

        self.tag_bold = self.textbuffer.create_tag("bold",  weight=Pango.Weight.BOLD)
        self.tag_italic = self.textbuffer.create_tag("italic", style=Pango.Style.ITALIC)
        self.tag_underline = self.textbuffer.create_tag("underline",  underline=Pango.Underline.SINGLE)
        self.tag_found = self.textbuffer.create_tag("found",  background="yellow")


    def bindWidgets(self):
        # self.root.bind('<Control-l>', lambda e: self.clear_viewer())
        pass


    def clear_viewer(self):
        # self.delete(1.0, END)
        # TODO: clear all history tags
        pass

    def parser(self, lst):
        # """
        # >>> obj = Viewer(parent=root)
        # >>> root.add(obj)
        # """
        # >>> data = [1, 'I001', 'hello', 'नमस्कार']
        # >>> obj.parser(data)
        # [1, 'I001', 'hello', 'नमस्कार']
        # """
        print(lst)
        word = lst[2]
        # # ahref = str(href)
        # # self.tag_config(ahref)
        # # self.tag_bind(ahref, "<Enter>", self._enter)
        # # self.tag_bind(ahref, "<Leave>", self._leave)
        # # self.tag_bind(ahref, "<Button-1>", lambda e: _click(e, href))
        # # self.tag_bind(ahref, "<Button-3>", lambda e: _click_secondary(e, href))
        # # self.insert(END, lst[2], ("h1", ahref))

        # buffer = "<b>%s</b>"%word
        # self.textbuffer.set_markup(buffer)

        start = self.textbuffer.get_end_iter()
        self.textbuffer.insert(start, word)

        end = self.textbuffer.get_end_iter()
        self.textbuffer.apply_tag(self.tag_bold, start, end)

        raw = lst[3]
        trasliterate = ""
        translations = []
        pos = "undefined"
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

        # self.insert(END, '\t['+trasliterate+']\n', "tsl")
        self.textbuffer.insert(end, '\t['+trasliterate+']\n')
        end = self.textbuffer.get_end_iter()

        for c, t in enumerate(translations):
            # self.insert(END, "%d. "%(c+1), "li")
            self.textbuffer.insert(end, "%4d. "%(c+1))
            end = self.textbuffer.get_end_iter()
            if t[0] == "": pos_ = "undefined"
            else: pos_ = t[0]

            self.textbuffer.insert(end, pos_.strip())
            end = self.textbuffer.get_end_iter()

            self.textbuffer.insert(end, " » ")
            end = self.textbuffer.get_end_iter()

            self.textbuffer.insert(end, t[1].strip()+"\n")
            end = self.textbuffer.get_end_iter()

            # print(self.textview.scroll_to_iter(end, 0, True, 1.0, 0.0 ))

        return [ t.strip() for p, t in translations ]

    def _autoscroll(self, *args):
        adj = self.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())


    def not_found(self, word):
        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert(end, "'%s' Not Found\n"%word)


        # self.config(state=NORMAL)
        # self.insert(END, word, "h1")
        # self.insert(END, " Not Found\n")
        # self.insert(END, "search: ", "em")
        # self.insert(END, "web", "web")
        # self.insert(END, " ")
        # self.insert(END, "other")
        # self.insert(END, "\n")
        # self.config(state=DISABLED)
        # self.tag_bind("web", "<Button-1>", lambda e: web_search(word))
        pass

    def _enter(self, event):
        # self.config(cursor="hand2")
        pass

    def _leave(self, event):
        # self.config(cursor="")
        pass


def _click(event, link):
    # ex = event.x_root
    # ey = event.y_root
    # href = Menu(tearoff=0)
    # href.add_command(label=link)
    # href.tk_popup(ex, ey)
    pass
_click_secondary=_click


def web_search(word):
    print("dummy %s.web_search()"%__name__)


def on_key_press(widget, event):
    # print(event.keyval)
    if event.keyval == 65307:
        Gtk.main_quit()


def main():
    global def_font
    def_font = ["DejaVuSansMono", 12, "normal"]

    global root
    root = Gtk.Window()
    root.connect('delete-event', Gtk.main_quit)
    root.connect('key_release_event', on_key_press)
    root.set_default_size(600, 300)


if __name__ == '__main__':
    main()
    import doctest
    doctest.testmod()
    obj = Viewer(parent=root)
    root.add(obj)
    data = [1, 'I001', 'hello', 'नमस्कार']
    obj.parser(data)
    # [1, 'I001', 'hello', 'नमस्कार']


    root.show_all()
    Gtk.main()
