#!/usr/bin/python3

from tkinter import *
from tkinter import ttk
#from tkinter.ttk import *
import tkinter.font as tkfont
from tkinter.simpledialog import askstring

import os, sys

filepath=os.path.abspath(__file__)
fullpath=os.path.dirname(filepath)

GLOSS=fullpath+"/foss_gloss/"

EN2NP=fullpath+"/foss_gloss/en2np.tra"
ABBR=fullpath+"/foss_gloss/en2np.abb"
TRANS=fullpath+"/foss_gloss/en2np.tsl"

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
        self.GLOSS=None

    def makeWidgets(self):
        # a treeview
        self.tree = ttk.Treeview(show="headings", columns=list_col[0])
        self.tree.config(selectmode='browse') #one select at the time

        self.tree.bind('<Button-3>', self.call_popup)
        self.tree.bind('<Key>', key_press)
        self.tree.bind('<Control-c>', clipboard)

        # TODO: open gloss keybind
        # self.tree.bind('<Control-u>', lambda e: self.opengloss)
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

    def fill_tree(self, gloss_file):
        self.GLOSS=gloss_file
        file=open(self.GLOSS, encoding="UTF-8").read().splitlines()
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
        popup.add_command(label="Open Directory", accelerator="Ctrl+o", command=open_dir)
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

    def opengloss(self):
        index=tablst.index(nb.select())
        os.system("setsid %s %s"%("leafpad", glist[index]))

def open_dir(*events):
    tab=nb.select()
    obj=tab_info[tab]
    gloss_file=obj.GLOSS
    os.system("setsid %s $(dirname %s)"%("nautilus", gloss_file))

def reload_gloss(self):
    tab=nb.select()
    index=tablst.index(tab)
    obj=tab_info[tab]
    obj.clear_tree()
    obj.fill_tree(glist[index])
    print("Reload %s"%glist[index])


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
        self.sbox.bind('<Up>', search_box_unfocus) #TODO: for upkey
        self.sbox.bind('<Down>', search_box_unfocus)
        self.sbox.bind('<Control-s>', search_box_emacs)
        self.sbox.bind('<Control-c>', lambda e: self.sbox.delete(0,END))
        #self.sbox.bind('<Control-a>', lambda e: self.sbox.select_range(0, END))


        self.sbox.bind('<Return>', search_from_box)
        self.sbox.bind('<Leave>', lambda e: root.bind('<Control-s>', search_box_emacs))

        self.master.bind('<Control-f>', search_box_focus)
        self.found_status=Label(self) #TODO: GUI status display

        var=IntVar() # TODO: autocopy to clipboard
        self.cbox_acopy = Checkbutton(self, text="auto copy", command=None, variable=var)
        self.cbox_acopy.config(background="#b2b2b2", relief=FLAT)
        var.set(1)

        #packing
        self.sbox.pack(expand=NO, side=RIGHT, fill=X)
        self.cbox_acopy.pack(side=LEFT)

    def search_box(self, *args):
        text=self.sbox.get()
        if text: search_from_box();

    def toggle_display(self, *args):
        if self.visible: self.pack_forget()
        else: self.pack(expand=NO, fill=X, side=TOP)
        self.visible = not self.visible

def search_box_focus(event):
    nav.sbox.focus()
    nav.sbox.select_range(0, END)
    root.unbind('<Control-s>')

def search_box_emacs(event):
    text=root.clipboard_get()
    if text=="" or text:
        nav.sbox.delete(0, END)
        nav.sbox.insert(0, text)
    else:
        nav.sbox.select_range(0, END)

def key_press(event):
    typed=event.char
    if not typed.isalpha(): return
    nav.sbox.delete(0, END)
    nav.sbox.insert(0, typed)
    nav.sbox.focus()

def search_from_box(*args):
    global word
    word=nav.sbox.get().lower().strip()

    global lang
    if word.isalpha(): lang=1;
    else: lang=2

    for i, obj in enumerate(glist):
        if search_tree(i, obj, word):
            return

    print("\"%s\" not found"%word)
    global ADD_LOCK
    ADD_LOCK=False

def search_tree(tab, obj, word):
    list = obj.tree.get_children()
    for item in list:
        sel=obj.tree.item(item)
        val=sel['values'][lang]
        if val==word:
            nb.select(tab)
            obj.tree.selection_set(item)
            obj.tree.focus(item)
            obj.tree.focus_set()
            obj.tree.yview(int(item[1:], 16)-1)
            return True
    return False

def add_to_list(*args):
    global ADD_LOCK, word
    if ADD_LOCK:
        print("World already Exist, only edit possible")
        return 1;

    DIRTY=True
    ADD_LOCK=True
    anubad=askstring("Entry", "अनुवाद: %s"%word)
    if not anubad: return

    en2np.count+=1
    row = [ en2np.count, word, anubad ]
    select=en2np.tree.insert('', 'end', values=row)
    # TODO: make class method do view
    en2np.tree.selection_set(select)
    en2np.tree.focus(select)
    en2np.tree.focus_set()
    en2np.tree.yview(int(select[1:], 16)-1)
    fp=open(EN2NP, 'a').write("\n"+word+": "+anubad)
    print(fp)

def clipboard(*args):
    obj=tab_info[nb.select()]
    sel=obj.tree.item(obj.tree.focus())
    val=sel['values']
    root.clipboard_clear()
    root.clipboard_append(val[2])
    print(val[2], "Copied to clipboard")

# def edit(*args):
#     print("Editing current value")
#     obj=tab_info[nb.select()]
#     sel=obj.tree.item(obj.tree.focus())
#     val=sel['values']
#     anubad=askstring("Modify", "Edit %s"%val[1])

def search_box_unfocus(*args):
    nav.sbox.select_range(0, 0)

    obj=tab_info[nb.select()]
    obj.tree.focus_set()
    item=obj.tree.next(obj.tree.focus())
    if not item: return
    obj.tree.selection_set(item)
    obj.tree.focus(item)
    obj.tree.focus_set()

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

def switch_tab(event):
    index=int(event.char)-1
    obj=glist[index]
    # BUG: object focus after tabswitch not working properly
    # print(index, tab, tab_info[tab])
    nb.select(index)
    obj.tree.focus(obj.tree.focus())

def load_files():
    global glist
    glist=[]
    top=1
    for file in os.listdir(GLOSS):
        if file[-4:] in [ ".tsl", ".fun", ".abb", ".tra" ]:
            obj=BrowseList()
            obj.fill_tree(GLOSS+file)
            nb.add(obj, text=file, underline=0, padding=3)
            glist.append(obj)
            if top < 10:
                root.bind('<Alt-KeyPress-%d>'%top, switch_tab)
            top+=1

if __name__ == '__main__':
    if len(sys.argv) > 1:
        cli_mode(sys.argv[1:])
        exit()

    root=Tk()
    root.title("anubad")
    nav=BrowseNav()
    nav.sbox.bind('<Control-i>', add_to_list)

    nb = ttk.Notebook()
    nb.pack(expand=YES, fill=BOTH )
    load_files()
    nb.enable_traversal()

    root.bind('<Control-s>', search_box_focus)
    root.bind('<Control-o>', open_dir)
    root.bind('<Key-F5>', reload_gloss)
    root.bind('<Control-Insert>', clipboard)
    root.bind('<Key-Escape>', lambda event: quit())
    root.bind('<Control-d>', lambda event: quit())
    root.mainloop()
