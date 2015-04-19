#!/usr/bin/python
# -*- coding: utf-8 -*-
# ^^^ needed for py2

"""
A module for the interactive text interface and Decoration.
"""

if __name__ == '__main__':
    exec(open("mysettings.conf").read())
    exec(open("gsettings.conf").read())
    sys.path.append(PATH_MYLIB)
    from debugly import *

try: #py2/3 compatibiliy
    from tkinter import *
    import tkinter.ttk as ttk
    import tkinter.font as font
except:
    from Tkinter import *
    import ttk


class Viewer(Text):
    def __init__(self, parent=None, root=None):
        Text.__init__(self, parent)
        self.root=root;
        self.makeWidgets()
        self.bindWidgets()

    def makeWidgets(self):
        self.config(height=12, width=60, takefocus=0)
        # TODO: retive font and avoid passing def_font, so that
        # def_font can be configure from object
        self.config(font=def_font[:2])
        self.tag_config("h1", font=def_font[:2] + ["bold"])
        self.tag_config("pos", foreground="red")
        self.tag_config("li", font=def_font[:2] + ["bold"], foreground="gray", lmargin1=20)
        self.tag_config("tsl", foreground="blue")

        self.tag_config("em", font=def_font[:2] + ["italic"], foreground="gray")

        self.tag_config("web", font=def_font[:2] + ["underline"], foreground="blue")
        self.tag_bind("web", "<Enter>", self._enter)
        self.tag_bind("web", "<Leave>", self._leave)


    def bindWidgets(self):
        self.root.bind('<Control-l>', lambda e: self.clear_viewer())


    def clear_viewer(self):
        self.config(state=NORMAL)
        self.delete(1.0, END)
        self.config(state=DISABLED)
        # TODO: clear all history tags

    def parser(self, lst):
        """
        >>> obj = Viewer(root=root)
        >>> obj.pack()
        >>> data = [1, 'I001', 'hello', 'नमस्कार']
        >>> obj.parser(data)
        [1, 'I001', 'hello', 'नमस्कार']
        """
        print(lst)
        href = lst[0:2]
        ahref = str(href)
        self.tag_config(ahref)
        self.tag_bind(ahref, "<Enter>", self._enter)
        self.tag_bind(ahref, "<Leave>", self._leave)
        self.tag_bind(ahref, "<Button-1>", lambda e: _click(e, href))
        self.tag_bind(ahref, "<Button-3>", lambda e: _click_secondary(e, href))

        self.config(state=NORMAL)
        self.insert(END, lst[2], ("h1", ahref))
        raw = lst[3]

        trasliterate = ""
        traslation = []
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
                traslation.append([pos, raw[fbreak:i]])
                fbreak = i+2
            elif c == ')':
                traslation.append([pos, raw[fbreak:i]])
                pos = ""
                fbreak = i+3
                level -= 1

        if i - fbreak > 2 or len(traslation) < 1:
            traslation.append([pos, raw[fbreak:]])

        self.insert(END, '\t['+trasliterate+']\n', "tsl")
        for c, t in enumerate(traslation):
            self.insert(END, "%d. "%(c+1), "li")
            if t[0] == "": pos_ = "undefined"
            else: pos_ = t[0]
            self.insert(END, pos_, "pos")
            self.insert(END, " ~ ")
            self.insert(END, t[1]+"\n")

        self.config(state=DISABLED)

    def not_found(self, word):
        self.config(state=NORMAL)
        self.insert(END, word, "h1")
        self.insert(END, " Not Found\n")
        self.insert(END, "search: ", "em")
        self.insert(END, "web", "web")
        self.insert(END, " ")
        self.insert(END, "other")
        self.insert(END, "\n")
        self.config(state=DISABLED)
        self.tag_bind("web", "<Button-1>", lambda e: web_search(word))

    def _enter(self, event):
        self.config(cursor="hand2")

    def _leave(self, event):
        self.config(cursor="")

def _click(event, link):
    ex = event.x_root
    ey = event.y_root
    href = Menu(tearoff=0)
    href.add_command(label=link)
    href.tk_popup(ex, ey)
_click_secondary=_click


def web_search(word):
    print("dummy %s.web_search()"%__name__)


def main():
    global def_font
    def_font = ["DejaVuSansMono", 12, "normal"]

    global root
    root = Tk()
    root.bind('<Key-Escape>', lambda event: quit())

if __name__ == '__main__':
    main()
    import doctest
    doctest.testmod()
    root.mainloop()
