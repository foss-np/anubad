#!/usr/bin/python
# -*- coding: utf-8 -*-
# ^^^ needed for py2

import os, sys
import copy

filepath = os.path.abspath(__file__)
fullpath = os.path.dirname(filepath) + '/'

exec(open(fullpath+"/gsettings.conf").read())

try: # py2/3 compatibility
    import tkinter as tk
    from tkinter import *
    from tkinter import ttk
    from tkinter.simpledialog import askstring
    exec(open(fullpath+"mysettings.conf").read())
except:
    import Tkinter as tk
    from Tkinter import *
    import ttk
    from tkSimpleDialog import askstring

if PATH_MYLIB:
    sys.path.append(PATH_MYLIB)
    from debugly import *

import browselst as BL
BL.def_font = def_font

import viewer as Vi
Vi.def_font = def_font

PATH_GLOSS = fullpath + PATH_GLOSS

#   ____ _   _ ___
#  / ___| | | |_ _|
# | |  _| | | || |
# | |_| | |_| || |
#  \____|\___/|___|

class GUI(Frame):
    def __init__(self, parent=None):
        Frame.__init__(self, parent)
        self.CURRENT_FOUND_ITEM = None
        self.MAIN_TAB = 0
        self.glist = []
        self.history = []

        self.makeWidgets()
        self.bindWidgets()
        self.pack(expand=NO, fill=X, side=TOP)

    def makeWidgets(self):
        # searchbox
        search_frame = LabelFrame(self, text="Search", padx=5, pady=5)
        combo_font = def_font[:]; combo_font[1]=11
        self.sbox = ttk.Combobox(search_frame, font=combo_font)
        self.sbox.insert(0, "Type your query here")

        var = IntVar() # TODO: autocopy to clipboard
        self.cbox_acopy = tk.Checkbutton(search_frame, text="auto copy")
        self.cbox_acopy.config(variable=var, takefocus=0)
        var.set(1)

        self.tabar = ttk.Notebook(takefocus=0)
        self.tabar.enable_traversal()

        self.viewer = Vi.Viewer(self, root)
        #self.viewer = Text(root)

        #packing
        self.sbox.pack(expand=YES, side=LEFT, fill=X)
        self.cbox_acopy.pack(side=RIGHT)
        search_frame.pack(expand=YES, side=TOP, fill=X)
        self.tabar.pack(expand=YES, fill=BOTH, side=BOTTOM)
        self.viewer.pack(expand=YES, fill=BOTH, side=BOTTOM)

    def bindWidgets(self):
        self.sbox.bind('<Control-c>', lambda e: self.sbox.delete(0, END))
        self.sbox.bind('<Control-g>', lambda e: self.sbox.delete(0, END))

        # TODO: will do the complete search
        self.sbox.bind('<Return>', sbox_next_search)

        self.sbox.bind('<FocusIn>', self.sboxFocusIn)
        self.sbox.bind('<FocusOut>', self.sboxFocusOut)
        self.sbox.bind('<Control-i>', add_to_list)

        root.bind('<Control-o>', self.open_dir)
        root.bind('<Control-u>', self.open_gloss)
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
        self.sbox.select_range(0, END)
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

    # TODO: add the decorator in all this stuffs :D
    def open_gloss(self, *events):
        tab = self.tabar.index(self.tabar.select())
        obj = self.glist[tab]
        arg = ""

        # TODO : smart xdg-open with arguments
        if jump:
            # ID = obj.tree.focus()
            arg = "--jump=%d"%(int(jump[1:], 16))

        os.system("setsid leafpad %s %s"%(arg, obj.GLOSS))


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
        # TODO: here prototype pattern can be applied
        # WISH: do the profile before and after
        # NOTE: some other patterns is here
        tab = 0
        for file_name in os.listdir(PATH_GLOSS):
            if not file_name[-4:] in FILE_TYPES: continue
            if "main" in file_name:
                self.MAIN_TAB = tab

            obj = BL.BrowseList(PATH_GLOSS+file_name)
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
    gui.sbox.delete(0, END)
    gui.sbox.insert(0, typed)
    gui.sbox.focus()
    root.unbind('<Key>')


def sbox_next_search(*args):
    ## TODO: Reverse search in nepali
    # grep might be useful for quick implementation
    word = gui.sbox.get().lower().strip()

    # TODO: Chain of Command Can be implimented
    id_lst = []
    for tab, obj in enumerate(gui.glist):
        ID = search_tree(tab, obj, word)
        if ID: id_lst.append((tab, ID))

    if not id_lst:
        print("\"%s\" not found"%word)
        gui.viewer.not_found(word)
        return

    gui.CURRENT_FOUND_ITEM = id_lst[0]
    gui.sbox.select_range(0, END)
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


def add_to_list(*args):
    word = gui.sbox.get().lower().strip()
    anubad = askstring("Entry", "anubad: %s"%word)
    if not anubad: return

    i = gui.tabar.index(gui.tabar.select())
    obj = gui.glist[i]

    obj.count += 1
    row = [obj.count, word, anubad]
    select = obj.tree.insert('', 'end', values=row)

    # TODO: make class method do view
    obj.tree.selection_set(select)
    obj.tree.focus(select)
    obj.tree.focus_set()
    obj.tree.yview(int(select[1:], 16)-1)
    fp = open(obj.GLOSS, 'a').write("\n" + word + "; " + anubad)
    print(fp)

def cli_mode(list):
    file = open(GLOSS).read()
    print("CLI-mode Currenly Disabled")
    # for word in list:
    #     found = file.find(word)
    #     if found == -1:
    #         print("%s Not Found"%word)
    #         break
    #     for i, char in enumerate(file[found:]):
    #         if char=='\n': break
    #         print(char)
    #     #os.system("echo %s | xclip -i"%file[found:found+i])
    #     print()

def main():
    if len(sys.argv) > 1:
        cli_mode(sys.argv[1:])
        exit()

    ## TODO: command line argument to ignore faulty gloss
    # -k ignore faulty gloss

    ## TODO: use parallel database & sync function
    # db design
    # {word, meaning, vote, link}

    # TODO: import mechanism
    # TODO: Ctrl+click follow the link

    global root
    root = Tk()
    root.title("anubad - अनुवाद")

    global gui
    gui = GUI()
    gui.load_files()
    root.update()

    gui.tabar.select(str(gui.MAIN_TAB))

    root.bind('<Key-Escape>', lambda event: quit())
    root.bind('<Control-d>', lambda event: quit())

if __name__ == '__main__':
    main()
    if PATH_PLUGINS:
        # TODO: trasliterate, espeak
        PATH_PLUGINS = fullpath + PATH_PLUGINS
        for file_name in os.listdir(PATH_PLUGINS):
            print(file_name, "loaded")
            exec(open(PATH_PLUGINS + file_name).read())

    root.mainloop()
