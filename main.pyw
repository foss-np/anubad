#!/usr/bin/python
# -*- coding: utf-8 -*-
# ^^^ needed for py2

import os, sys
import copy

try: # py2/3 compatibility
    import tkinter as tk
    from tkinter import *
    from tkinter import ttk
    from tkinter.ttk import *
    from tkinter.simpledialog import askstring
except:
    import Tkinter as tk
    from Tkinter import *
    import ttk
    from ttk import *
    from tkSimpleDialog import askstring

filepath = os.path.abspath(__file__)
fullpath = os.path.dirname(filepath)

exec(open(fullpath+"/settings.conf").read())
exec(open(fullpath+"/my.conf").read())
PATH_GLOSS = fullpath+PATH_GLOSS

import browselst as BL
from browselst import *
BL.def_font=def_font

import viewer as Vi
from viewer import *
Vi.def_font=def_font

DIRTY = False
ADD_LOCK = True

#   ____ _   _ ___
#  / ___| | | |_ _|
# | |  _| | | || |
# | |_| | |_| || |
#  \____|\___/|___|

class GUI(Frame):
    def __init__(self, parent=None):
        Frame.__init__(self, parent)
        self.visible = True
        self.glist = []
        self.word = []
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

        self.nb = ttk.Notebook(takefocus=0)
        self.nb.enable_traversal()

        self.out = Viewer(self, root)

        #packing
        self.sbox.pack(expand=YES, side=LEFT, fill=X)
        self.cbox_acopy.pack(side=RIGHT)
        search_frame.pack(expand=YES, side=TOP, fill=X)
        self.nb.pack(expand=YES, fill=BOTH, side=BOTTOM)
        self.out.pack(expand=YES, fill=BOTH, side=BOTTOM)

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
        self.nb.select(tab)
        obj.treeSetFocus()

    # TODO: add the decorator in all this stuffs :D
    def open_gloss(self, *events):
        index = self.nb.index(self.nb.select())
        obj = self.glist[index]
        os.system("setsid %s %s"%("leafpad", obj.GLOSS))

    def open_dir(self, *events):
        index = self.nb.index(self.nb.select())
        obj = self.glist[index]
        os.system("setsid %s %s"%(FILEMGR, obj.GLOSS))

    def reload_gloss(self, *events):
        index = self.nb.index(self.nb.select())
        obj = self.glist[index]
        obj.reload_tree()
        print("Reload %s"%obj.GLOSS)

    def load_files(self):
        # TODO: here prototype pattern can be applied
        # WISH: do the profile before and after
        for i, file in enumerate(os.listdir(PATH_GLOSS)):
            if not file[-4:] in FILE_TYPES: continue
            obj = BrowseList(PATH_GLOSS+file)
            self.nb.add(obj, text=file, padding=3)
            self.glist.append(obj)
            if i < 10:
                root.bind('<Alt-KeyPress-%d>'%(i+1), self.switch_tab)

        return self.glist

    def load_files_prototype_pattern(self):
        ori_obj = BrowseList()

        for i, file in enumerate(os.listdir(PATH_GLOSS)):
            if not file[-4:] in FILE_TYPES: continue
            obj = copy.deepcopy(ori_obj)
            obj.GLOSS = PATH_GLOSS+file
            obj.fill_tree(PATH_GLOSS+file)
            self.nb.add(obj, text=file, padding=3)
            self.glist.append(obj)
            if i < 10:
                root.bind('<Alt-KeyPress-%d>'%(i+1), self.switch_tab)

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
    global word
    word = gui.sbox.get().lower().strip()

    if word.isalpha(): lang = 1;
    else: lang = 2

    flag = False

    # TODO: Chain of Command Can be implimented
    gui.sbox.select_range(0, END)
    for i, obj in enumerate(gui.glist):
        flag = search_tree(i, obj, word, lang) or flag

    if not flag:
        print("\"%s\" not found"%word)
        gui.out.not_found(word)

    global ADD_LOCK
    ADD_LOCK = False

def search_tree(tab, obj, word, lang):
    list = obj.tree.get_children()
    for item in list:
        sel = obj.tree.item(item)
        if sel['values'][lang] == word:
            gui.out.parser([tab, item]+sel['values'][1:])
            gui.word.append(word)
            gui.sbox.config(values=gui.word)
            return True
    return False

# NOTE: this is decorator pattern
def _click(event, href):
    gui.nb.select(href[0])
    obj = gui.glist[href[0]]
    obj.tree.selection_set(href[1])
    obj.tree.focus(href[1])
    obj.tree.focus_set()
    root.update()
    obj.tree.yview(int(href[1][1:], 16)-1)

Vi._click=_click

def add_to_list(*args):
    global ADD_LOCK, word

    if ADD_LOCK:
        print("World already Exist, only edit possible")
        return 1;

    DIRTY = True
    ADD_LOCK = True
    anubad = askstring("Entry", "anubad: %s"%word)
    if not anubad: return

    i = gui.nb.index(gui.nb.select())
    obj = gui.glist[i]

    obj.count += 1
    row = [obj.count, word, anubad]
    select = obj.tree.insert('', 'end', values=row)

    # TODO: make class method do view
    obj.tree.selection_set(select)
    obj.tree.focus(select)
    obj.tree.focus_set()
    obj.tree.yview(int(select[1:], 16)-1)
    fp = open(obj.GLOSS, 'a').write("\n"+word+"; "+anubad)
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

#  _  __                 _
# (_)/ _|_ __ ___   __ _(_)_ __
# | | |_| '_ ` _ \ / _` | | '_ \
# | |  _| | | | | | (_| | | | | |
# |_|_| |_| |_| |_|\__,_|_|_| |_|

if __name__ == '__main__':
    if len(sys.argv) > 1:
        cli_mode(sys.argv[1:])
        exit()

    # TODO: memory list (or scroll the textbox)
    # search history

    # TODO: command line argument to ignore faulty gloss
    # -k ignore faulty gloss

    # TODO: use parallel database & sync function
    # db design
    # {word, meaning, vote, link}

    # TODO: plugin module: trasliterate validity test

    root = Tk()
    root.title("anubad - आनुबाद")

    # BL.root = root
    # Vi.root = root

    gui = GUI()
    gui.load_files()
    #gui.load_files_prototype_pattern()
    gui.glist[0].treeSetFocus()

    root.bind('<Key-Escape>', lambda event: quit())
    root.bind('<Control-d>', lambda event: quit())

    # TODO: auto-add plug-ins
    exec(open(fullpath+"/plug_ins/dicts.py").read())

    root.mainloop()
