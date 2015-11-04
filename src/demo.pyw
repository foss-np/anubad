#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ^^^ needed for py2

import os, sys

filepath = os.path.abspath(__file__)
fullpath = os.path.dirname(filepath) + '/'

exec(open(fullpath+"/gsettings.conf").read())
exec(open(fullpath + "mysettings.conf").read())

try: # py2/3 compatibility
    import tkinter as tk
    from tkinter.ttk import *
except:
    import Tkinter as tk
    from ttk import *


tmp = def_FONT.split()
def_FONT = [ ' '.join(tmp[:-1]), tmp[-1] ]
FILE_TYPES = ["tsl", "fun", "abb", "tra", "txt"]
PATH_GLOSS = fullpath + PATH_GLOSS + LIST_GLOSS[0]

#  ____
# | __ ) _ __ _____      _____  ___ _ __
# |  _ \| '__/ _ \ \ /\ / / __|/ _ \ '__|
# | |_) | | | (_) \ V  V /\__ \  __/ |
# |____/|_|  \___/ \_/\_/ |___/\___|_|
#

class Browser(Frame):
    cols = ["#", "en", "ne"]

    col_attrib = [
       #["id", "label", min-width, width, stretch, !show],
        ["#", "#", 50, 50, 0, False],
        ["en", "English", 90, 90, 1, False],
        ["ne", "नेपाली", 250, 170, 1, False]
    ]

    def __init__(self, parent=None, gloss=None):
        Frame.__init__(self, parent)
        self.GLOSS = gloss

        self.makeWidgets()

        if self.GLOSS: # avoid utf-8 print in terminal
            self.fill_tree(self.GLOSS)

        self.pack(expand=1, side="top", fill="both", anchor="n")


    def makeWidgets(self):
        # a treeview
        self.tree = Treeview(self, show="headings", columns=Browser.cols)
        self.tree.grid(column=0, row=0, sticky='news', in_=self)
        self.tree.config(selectmode="browse")
        self.tree.tag_configure("npfont", font=def_FONT)

        # adding header
        for a in Browser.col_attrib:
            if a[-1]: continue
            self.tree.heading(a[0], text=a[1])
            self.tree.column(a[0], minwidth=a[2], width=a[3], stretch=a[4])

        # adding scrollbar
        vsb = Scrollbar(self, orient="vertical", command=self.tree.yview)
        vsb.config(takefocus=0)
        vsb.grid(column=1, row=0, sticky='ns', in_=self)

        hsb = Scrollbar(self, orient="horizontal", command=self.tree.xview)
        hsb.config(takefocus=0)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        hsb.grid(column=0, row=1, sticky='ew', in_=self)

        # grid config
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)


    def fill_tree(self, _gloss):
        try: # py2/3 compatibility
            data = open(self.GLOSS, encoding="UTF-8").read()
        except:
            # for python2
            data = open(self.GLOSS).read()
            data = data.decode('utf-8')

        self.count = 0
        for line in data.splitlines():
            self.count += 1
            row = line.split(';')
            row.insert(0, self.count)
            try:
                row[2] = row[2][1:] # remove space
            except:
                print("File Format Error: %s: %d"%(self.GLOSS, self.count))
                exit()
            self.select = self.tree.insert('', 'end', values=row, tag="npfont")


    def treeSetFocus(self):
        if not self.count: return # if no data
        if self.tree.focus() == "":
            #print("%5d"%self.count, self.GLOSS.split('/')[-1])
            self.tree.selection_set('I001')
            self.tree.focus('I001')

        self.tree.focus_set()


    def get_ID_below_mouse(self, event):
        HEIGHT = 19
        offset = HEIGHT * 18
        ex, ey = event.x_root, event.y_root - offset
        ID = Treeview.identify(self.tree, component='item', x=ex, y=ey)

        self.tree.selection_set(ID)
        self.tree.focus(ID)
        self.tree.focus_set()

        return ID

#        _
# __   _(_) _____      _____ _ __
# \ \ / / |/ _ \ \ /\ / / _ \ '__|
#  \ V /| |  __/\ V  V /  __/ |
#   \_/ |_|\___| \_/\_/ \___|_|
#

class Viewer(tk.Text):
    def __init__(self, parent=None):
        tk.Text.__init__(self, parent)

        self.makeWidgets()


    def makeWidgets(self):
        self.config(height=12, width=60, takefocus=0)
        self.config(font=def_FONT)
        self.tag_config("h1", font=def_FONT + ["bold"])
        self.tag_config("pos", foreground="red")
        self.tag_config("li", font=def_FONT + ["bold"], foreground="gray", lmargin1=20)
        self.tag_config("tsl", foreground="blue")


    def clear_viewer(self):
        self.config(state="normal")
        self.delete(1.0, "end")
        self.config(state="disabled")


    def parse(self, lst, obj):
        raw = lst[3]
        transliterate = ""
        translation = []
        pos = "undefined"
        level = 0

        fbreak = ftsl = 0
        for i, c in enumerate(raw):
            if c == '[': ftsl = i; level += 1
            elif c == ']':
                transliterate = raw[ftsl+1:i]
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
                translation.append([pos, raw[fbreak:i]])
                fbreak = i+2
            elif c == ')':
                translation.append([pos, raw[fbreak:i]])
                pos = ""
                fbreak = i+3
                level -= 1

        if i - fbreak > 2 or len(translation) < 1:
            translation.append([pos, raw[fbreak:]])

        href = lst[0:2]
        ahref = str(href)
        self.tag_config(ahref)
        self.tag_bind(ahref, "<Enter>", lambda e: self.config(cursor="hand2"))
        self.tag_bind(ahref, "<Leave>", lambda e: self.config(cursor=""))
        self.tag_bind(ahref, "<Button-1>", lambda e: self._click(e, obj, href))

        self.config(state="normal")
        self.insert("end", lst[2], ("h1", ahref))

        self.insert("end", '\t['+transliterate+']\n', "tsl")
        for c, t in enumerate(translation):
            self.insert("end", "%d. "%(c+1), "li")
            if t[0] == "": pos_ = "undefined"
            else: pos_ = t[0]
            self.insert("end", pos_, "pos")
            self.insert("end", " » ")
            self.insert("end", t[1]+"\n")

        self.config(state="disabled")


    def not_found(self, word):
        self.config(state="normal")
        self.insert("end", word, "h1")
        self.insert("end", " Not Found\n")
        self.config(state="disabled")


    def _click(self, event, obj, href):
        obj.tree.selection_set(href[1])
        obj.tree.focus(href[1])
        obj.tree.focus_set()
        obj.tree.yview(int(href[1][1:], 16)-1)

#   ____ _   _ ___
#  / ___| | | |_ _|
# | |  _| | | || |
# | |_| | |_| || |
#  \____|\___/|___|
#

class GUI(tk.Frame):
    def __init__(self, parent=None):
        tk.Frame.__init__(self, parent)
        self.parent = parent

        self.MAIN_TAB = 0
        self.glist = []
        self.history = []

        self.makeWidgets()

        self.pack(expand=1, fill="both")
        self.sbox.focus()

    def makeWidgets(self):
        # searchbox
        f = tk.Frame(self)
        f.pack(expand=0, fill="x")

        Label(f, text="Query").pack(side="left", padx=5)

        combo_font = def_FONT[:]; combo_font[1]=11
        self.sbox = Combobox(f, font=combo_font)
        self.sbox.pack(side="left")
        self.sbox.bind('<Control-c>', lambda e: self.sbox.delete(0, "end"))
        self.sbox.bind('<Return>', self.sbox_next_search)
        self.parent.bind('<Control-f>', self.sboxSetFocus)

        # viewer
        self.viewer = Viewer(self)
        self.viewer.pack(expand=1, fill="both")
        self.viewer.bind('<Control-l>', lambda e: self.viewer.clear_viewer())

        # notebook
        self.tabar = Notebook(self, takefocus=0)
        self.tabar.pack(expand=1, fill="both")
        self.tabar.enable_traversal()


    def sboxSetFocus(self, event):
        self.sbox.focus()
        self.sbox.select_range(0, "end")


    def switch_tab(self, *event):
        tab = int(event[0].char)-1
        obj = self.glist[tab]
        self.tabar.select(tab)
        obj.treeSetFocus()


    def load_files(self):
        tab = 0
        for file_name in os.listdir(PATH_GLOSS):
            if not file_name[-3:] in FILE_TYPES: continue
            if "main" in file_name:
                self.MAIN_TAB = tab

            obj = Browser(self.parent, PATH_GLOSS+file_name)
            obj.tree.bind('<Double-Button-1>', self._doubleClick)
            self.tabar.add(obj, text=file_name, padding=3)
            self.glist.append(obj)

            if tab < 9:
                self.parent.bind('<Alt-KeyPress-%d>'%(tab+1), self.switch_tab)
            tab += 1

        self.tabar.select(str(self.MAIN_TAB))
        return self.glist

    def sbox_next_search(self, *args):
        word = self.sbox.get().lower().strip()
        id_lst = []
        for tab, obj in enumerate(self.glist):
            FOUND = False
            for item_ID in obj.tree.get_children():
                item = obj.tree.item(item_ID)
                if item['values'][1] != word: continue
                self.viewer.parse([tab, item_ID] + item['values'][1:], obj)
                FOUND = item_ID
            if FOUND: id_lst.append((tab, FOUND))

        if not id_lst:
            self.viewer.not_found(word)
            return

        self.sbox.select_range(0, "end")
        self.history.append(word)
        self.sbox.config(values=self.history)


    def _doubleClick(self, event):
        tab = self.tabar.index(self.tabar.select())
        obj = self.glist[tab]
        ID = obj.get_ID_below_mouse(event)
        item = obj.tree.item(ID)
        self.viewer.parse([tab, ID] + item['values'][1:], obj)


def main():
    root = tk.Tk()
    root.title("anubad - अनुवाद")

    gui = GUI(root)
    gui.load_files()
    root.update()

    root.bind('<Key-Escape>', lambda event: quit())

    style = Style(root)
    style.theme_use("clam")
    return root


if __name__ == '__main__':
    main().mainloop()
