#!/usr/bin/python3

from tkinter import *
from tkinter import ttk
#from tkinter.ttk import *
import tkinter.font as tkfont
from tkinter.simpledialog import askstring

import os, sys

filepath=os.path.abspath(__file__)
fullpath=os.path.dirname(filepath)
#print(fullpath)

GLOSS=fullpath+"/foss_gloss/glossary.list"
import ttksearchbox.main as ttksbox

list_col = [
    ["#", "Word", "नेपाली"],
    [50, 250, 250]
]

DIRTY=False
ADD_LOCK=True

def_font=[ "DejaVuSansMono", 11 ]

class BrowseList(Frame):
    def __init__(self, parent=None):
        Frame.__init__(self, parent)
        self.visible = True
        self.makeWidgets()
        self.pack(expand=YES, side=TOP, fill=BOTH, anchor=N)
        self.popup=None
        self.make_popup()


    def makeWidgets(self):
        # a treeview
        self.tree = ttk.Treeview(show="headings", columns=list_col[0])
        self.tree.config(selectmode='browse') #one select at the time
        self.tree.bind('<Button-3>', self.call_popup)
        #self.tree.config(height=8) #def=10
        #self.tree.config(height=8, font=[ "DejaVuSansMono", 11 ])

        # adding header
        for c, w in zip(list_col[0], list_col[1]):
            self.tree.heading(c, text=c, command=lambda col=c: self.sortby(col, 0))
            self.tree.column(c, width=w, minwidth=w)

        # adding scrollbar
        vsb = Scrollbar(orient="vertical", command=self.tree.yview, takefocus=0)
        hsb = Scrollbar(orient="horizontal", command=self.tree.xview, takefocus=0)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # packing to grid
        self.tree.grid(column=0, row=0, sticky='news', in_=self)
        vsb.grid(column=1, row=0, sticky='ns', in_=self)
        hsb.grid(column=0, row=1, sticky='ew', in_=self)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def sortby(self, col, descending): #column click sort
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]

        data.sort(reverse=descending)
        for i, item in enumerate(data):
            self.tree.move(item[1], '', i)

        # switch the heading so that it will sort in the opposite direction
        self.tree.heading(col,
            command=lambda col=col: self.sortby(col, int(not descending)))

    def fill_tree(self):
        file=open(GLOSS, encoding="UTF-8").read().splitlines()
        self.count=0
        def insert_row(line):
            self.count+=1
            row=line.split(':')
            row.insert(0, self.count)
            row[2]=row[2][1:]
            id=self.tree.insert('', 'end', values=row)
            return id

        select=insert_row(file[0])

        for line in file[1:]:
            insert_row(line)

        if self.count:
            #show_count(count)
            self.tree.selection_set(select)
            self.tree.focus(select)
            self.tree.focus_set()

    def clear_tree(self):
        x = self.tree.get_children()
        for item in x: self.tree.delete(item)

    def toggle_display(self, *args):
        if self.visible: self.pack_forget()
        else: self.pack(expand=NO, side=TOP, fill=BOTH, anchor=N)
        self.visible = not self.visible

    def make_popup(self):
        popup = Menu(self, tearoff=0)

        popup.add_command(label="Edit", command=None)
        popup.add_command(label="Open Directory", command=self.opendir)
        popup.add_command(label="Open Gloss", command=self.opengloss)
        popup.add_separator()
        popup.add_command(label="Reload", command=None)
        self.popup=popup

    def call_popup(self, event):
        global POP_SELECT
        ex=event.x_root
        ey=event.y_root
        offset=19*3
        self.popup.tk_popup(ex,ey)
        POP_SELECT=ttk.Treeview.identify(self.tree, component='item', x=ex, y=ey-offset)
        self.tree.selection_set(POP_SELECT)
        self.tree.focus(POP_SELECT)
        self.tree.focus_set()

    def opendir(self):
        os.system("setsid %s $(dirname %s)"%("nautilus", GLOSS))

    def opengloss(self):
        os.system("setsid %s %s"%("leafpad", GLOSS))



class BrowseNav(Frame):
    def __init__(self, parent=None):
        Frame.__init__(self, parent)
        self.visible = True
        self.makeWidgets()
        self.pack(expand=NO, fill=X, side=TOP)
        self.config(background="#b2b2b2")

    def makeWidgets(self):
        # searchbox
        ttksbox.entrystyle()
        self.sbox=ttksbox.ttk.Entry(self, style="Search.entry", width=20)
        self.sbox.insert(0, "Search")
        self.sbox.bind('<Button-1>', self.search_box)
        self.sbox.bind('<Up>', search_box_unfocus)
        self.sbox.bind('<Down>', search_box_unfocus)

        self.master.bind('<Control-s>', self.search_box)
        self.master.bind('<Control-f>', self.search_box)
        self.found_status=Label(self)

        #packing
        self.sbox.pack(expand=NO, side=RIGHT, fill=X)


    def search_box(self, *args):
        self.sbox.focus()
        self.sbox.select_range(0, END)

    def toggle_display(self, *args):
        if self.visible: self.pack_forget()
        else: self.pack(expand=NO, fill=X, side=TOP)
        self.visible = not self.visible

def search_from_box(*args):
    list = blst.tree.get_children()
    word=nav.sbox.get().lower().strip()

    if word.isalpha(): lang=1;
    else: lang=2

    for item in list:
        sel=blst.tree.item(item)
        val=sel['values'][lang]
        if val==word:
            blst.tree.selection_set(item)
            blst.tree.focus(item)
            blst.tree.focus_set()
            blst.tree.yview(int(item[1:], 16)-1)
            break
    else:
        print("\"%s\" not found"%word)
        global ADD_LOCK
        ADD_LOCK=False

def add_to_list(*args):
    global ADD_LOCK
    if ADD_LOCK:
        print("World already Exist, only edit possible")
        return 1;

    DIRTY=True
    ADD_LOCK=True
    word=nav.sbox.get().lower()
    anubad=askstring("Entry", "अनुवाद: %s"%word)
    if not anubad: return

    blst.count+=1
    row = [ blst.count, word, anubad ]
    select=blst.tree.insert('', 'end', values=row)
    blst.tree.selection_set(select)
    blst.tree.focus(select)
    blst.tree.focus_set()
    blst.tree.yview(int(select[1:], 16)-1)
    fp=open(GLOSS, 'a').write("\n"+word+": "+anubad)

def clipboard(*args):
    print("Copy current view to clipboard")
    sel=blst.tree.item(blst.tree.focus())
    val=sel['values']
    root.clipboard_clear()
    root.clipboard_append(val[2])

def edit(*args):
    print("Editing current value")
    sel=blst.tree.item(blst.tree.focus())
    val=sel['values']
    anubad=askstring("Modify", "Edit %s"%val[1])

def search_box_unfocus(*args):
    blst.tree.focus_set()


def cli_mode(list):
    file=open(GLOSS).read()#.splitlines()
    for word in list:
        found=file.find(word)
        if found == -1:
            print("%s Not Found"%word)
            break
        for i, char in enumerate(file[found:]):
            if char=='\n': break
            print(char, end="")
        #os.system("echo %s | xclip -i"%file[found:found+i])

        print()

if __name__=="__main__":
    if len(sys.argv) > 1:
        cli_mode(sys.argv[1:])
        exit()

    root=Tk()
    root.title("anubad")

    nav=BrowseNav()
    nav.sbox.bind('<Return>', search_from_box)
    nav.sbox.bind('<Control-a>', add_to_list)
    blst=BrowseList();
    blst.fill_tree()

    root.bind('<Control-c>', clipboard)
    root.bind('<Control-e>', edit)
    root.bind("<Key-Escape>", lambda event: quit())
    root.bind('<Control-d>', lambda event: quit())
    root.mainloop()
