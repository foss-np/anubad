#!/usr/bin/python
# -*- coding: utf-8 -*-
# ^^^ needed for py2

import os, sys

filepath = os.path.abspath(__file__)
fullpath = os.path.dirname(filepath) + '/'

exec(open(fullpath+"/gsettings.conf").read())

try: # py2/3 compatibility
    import tkinter as tk
    from tkinter.ttk import *
    from tkinter.simpledialog import askstring
    exec(open(fullpath + "mysettings.conf").read())
except:
    import Tkinter as tk
    from ttk import *
    from tkSimpleDialog import askstring

if PATH_MYLIB and os.path.isdir(PATH_MYLIB):
    sys.path.append(PATH_MYLIB)
    from debugly import *

import browselst as BL
import viewer as Vi

tmp = def_FONT.split()
def_FONT = [ ' '.join(tmp[:-1]), tmp[-1], "normal" ]

BL.def_font = def_FONT
Vi.def_font = def_FONT

PATH_GLOSS = fullpath + PATH_GLOSS + LIST_GLOSS[0]

#   ____ _   _ ___
#  / ___| | | |_ _|
# | |  _| | | || |
# | |_| | |_| || |
#  \____|\___/|___|

class GUI(Frame):
    def __init__(self, parent=None):
        Frame.__init__(self, parent)
        self.CURRENT_FOUND_ITEM = False
        self.MAIN_TAB = 0
        self.glist = []
        self.history = []

        self.makeWidgets()
        self.bindWidgets()
        self.pack(expand=1, fill="both")

    def makeWidgets(self):
        # searchbox
        button_frame = Frame(self)
        button_frame.pack(expand=1, fill="both")

        Label(button_frame, text="Query").pack(side="left", padx=5)

        combo_font = def_FONT[:]; combo_font[1]=11
        self.sbox = Combobox(button_frame, font=combo_font)
        self.sbox.pack(side="left")
        self.sbox.insert(0, "Here")

        # viewer
        view_frame = Frame(self)
        view_frame.pack(expand=1, side="right", fill="both")

        self.viewer = Vi.Viewer(view_frame, root)
        self.viewer.pack(expand=1, side="top", fill="both")

        self.tabar = Notebook(view_frame, takefocus=0)
        self.tabar.pack(expand=1, side="top", fill="both")
        self.tabar.enable_traversal()


    def bindWidgets(self):
        self.sbox.bind('<Control-c>', lambda e: self.sbox.delete(0, "end"))
        self.sbox.bind('<Control-g>', lambda e: self.sbox.delete(0, "end"))

        self.sbox.bind('<Return>', sbox_next_search)

        self.sbox.bind('<FocusIn>', self.sboxFocusIn)
        self.sbox.bind('<FocusOut>', self.sboxFocusOut)
        self.sbox.bind('<Control-i>', add_to_list)

        root.bind('<Control-o>', self.open_dir)
        root.bind('<Key-F5>', self.reload_gloss)

        root.bind('<Control-f>', self.sboxSetFocus)
        root.bind('<Control-s>', self.sboxSetFocus)
        root.bind('<Key>', key_press)

    def sboxFocusIn(self, event):
        gui.sbox.focus()
        root.unbind('<Control-s>')
        root.bind('<Control-s>', self.sbox_emacs_search_next)

    def sboxFocusOut(self, event):
        root.unbind('<Control-c>')
        root.bind('<Key>', key_press)
        root.bind('<Control-s>', self.sboxSetFocus)

    def sboxSetFocus(self, event):
        self.sbox.focus()
        self.sbox.select_range(0, "end")
        root.unbind('<Control-s>')

    def sbox_emacs_search_next(self, event):
        sbox_text = self.sbox.get()
        if sbox_text:
            sbox_next_search();
        else: # if empty get from clipboard
            clip_text = root.clipboard_get()
            if clip_text:
                self.sbox.insert(0, clip_text)

    def toggle_display(self, *args):
        if self.visible: self.pack_forget()
        else: self.pack(expand=NO, fill=X, side=TOP)
        self.visible = not self.visible

    def switch_tab(self, *event):
        tab = int(event[0].char)-1
        obj = self.glist[tab]
        # BUG: object focus after tabswitch not working properly
        # print(index, tab, tab_info[tab])
        self.tabar.select(tab)
        obj.treeSetFocus()

    def open_dir(self, *events):
        tab = self.tabar.index(self.tabar.select())
        obj = self.glist[tab]
        os.system("setsid nemo %s"%obj.GLOSS)

    def reload_gloss(self, *events):
        tab = self.tabar.index(self.tabar.select())
        obj = self.glist[tab]
        obj.reload_tree()
        print("Reload %s"%obj.GLOSS)

    def load_files(self):
        tab = 0
        for file_name in os.listdir(PATH_GLOSS):
            if not file_name[-4:] in FILE_TYPES: continue
            if "main" in file_name:
                self.MAIN_TAB = tab

            obj = BL.BrowseList(root, PATH_GLOSS+file_name)
            obj.tree.bind('<Double-Button-1>', _doubleClick)
            self.tabar.add(obj, text=file_name, padding=3)
            self.glist.append(obj)

            if tab < 9:
                root.bind('<Alt-KeyPress-%d>'%(tab+1), self.switch_tab)
            tab += 1

        return self.glist

#        _   _                  __                  _   _
#   ___ | |_| |__   ___ _ __   / _|_   _ _ __   ___| |_(_) ___  _ __
#  / _ \| __| '_ \ / _ \ '__| | |_| | | | '_ \ / __| __| |/ _ \| '_ \
# | (_) | |_| | | |  __/ |    |  _| |_| | | | | (__| |_| | (_) | | | |
#  \___/ \__|_| |_|\___|_|    |_|  \__,_|_| |_|\___|\__|_|\___/|_| |_|

def key_press(event):
    typed = event.char
    if not typed.isalpha(): return
    gui.sbox.delete(0, "end")
    gui.sbox.insert(0, typed)
    gui.sbox.focus()
    root.unbind('<Key>')


def sbox_next_search(*args):
    word = gui.sbox.get().lower().strip()
    id_lst = []
    for tab, obj in enumerate(gui.glist):
        ID = search_tree(tab, obj, word)
        if ID: id_lst.append((tab, ID))

    if not id_lst:
        print("\"%s\" not found"%word)
        gui.viewer.not_found(word)
        return

    gui.CURRENT_FOUND_ITEM = id_lst[0]
    gui.sbox.select_range(0, "end")
    gui.history.append(word)
    gui.sbox.config(values=gui.history)


def search_tree(tab, obj, word):
    for item_ID in obj.tree.get_children():
        item = obj.tree.item(item_ID)
        if item['values'][1] != word: continue
        gui.viewer.parser([tab, item_ID] + item['values'][1:])
        return item_ID
    return False

# NOTE: this is not the decorator pattern
def _click(event, href):
    gui.tabar.select(href[0])
    obj = gui.glist[href[0]]
    obj.tree.selection_set(href[1])
    obj.tree.focus(href[1])
    obj.tree.focus_set()
    root.update()
    obj.tree.yview(int(href[1][1:], 16)-1)
Vi._click = _click


def _doubleClick(event):
    tab = gui.tabar.index(gui.tabar.select())
    obj = gui.glist[tab]
    ID = obj.get_ID_below_mouse(event)
    item = obj.tree.item(ID)
    gui.viewer.parser([tab, ID] + item['values'][1:])


def add_to_list(*args):
    word = gui.sbox.get().lower().strip()
    anubad = askstring("Entry", "anubad: %s"%word)
    if not anubad: return

    i = gui.tabar.index(gui.tabar.select())
    obj = gui.glist[i]

    obj.count += 1
    row = [obj.count, word, anubad]
    select = obj.tree.insert('', 'end', values=row)

    obj.tree.selection_set(select)
    obj.tree.focus(select)
    obj.tree.focus_set()
    obj.tree.yview(int(select[1:], 16)-1)
    fp = open(obj.GLOSS, 'a').write("\n" + word + "; " + anubad)
    print(fp)


def main():
    global root
    root = tk.Tk()
    root.title("anubad - अनुवाद")

    global gui
    gui = GUI()
    gui.load_files()
    root.update()

    gui.tabar.select(str(gui.MAIN_TAB))

    root.bind('<Key-Escape>', lambda event: quit())
    root.bind('<Control-d>', lambda event: quit())

    style = Style(root)
    style.theme_use("clam")


if __name__ == '__main__':
    main()
    root.mainloop()
