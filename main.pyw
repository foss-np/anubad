#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys

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

import ttksearchbox.main as ttksbox

filepath=os.path.abspath(__file__)
fullpath=os.path.dirname(filepath)

exec(open(fullpath+"/settings.conf").read())
PATH_GLOSS=fullpath+PATH_GLOSS

DIRTY=False
ADD_LOCK=True

cols = [ "#", "en", "ne" ]

col_attrib = [
   #[ "id", "label", min-width, width, stretch, !show ],
    [ "#", "#", 50, 50, 0, False ],
    [ "en", "English", 250, 300, 1, False ],
    [ "ne", "नेपाली", 250, 90, 1, False ]
]

class BrowseList(Frame):
    def __init__(self, _gloss=None, parent=None):
        Frame.__init__(self, parent)
        self.visible = True
        self.popup=None
        self.makeWidgets(cols, col_attrib)
        self.bindWidgets()
        self.GLOSS=_gloss
        if self.GLOSS:
            # avoid utf-8 print in terminal
            print("loading", self.GLOSS.split('/')[-1])
            self.fill_tree(self.GLOSS)

        self.pack(expand=YES, side=TOP, fill=BOTH, anchor=N)
        self.make_popup()

    def makeWidgets(self, _c, _a):
        # a treeview
        self.tree = ttk.Treeview(self, show="headings", columns=_c)
        self.tree.config(selectmode="browse")

        #self.tree.config(height=8) #def=10
        #self.tree.config(height=8, font=[ "DejaVuSansMono", 11 ])

        # adding header
        for a in _a:
            if a[-1]: continue
            self.tree.heading(a[0], text=a[1], command=lambda aa=a[0]: self.sortby(aa, 0))
            self.tree.column(a[0], minwidth=a[2], width=a[3], stretch=a[4])

        # adding scrollbar
        vsb = Scrollbar(self, orient="vertical", command=self.tree.yview, takefocus=0)
        hsb = Scrollbar(self, orient="horizontal", command=self.tree.xview, takefocus=0)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # packing to grid
        self.tree.grid(column=0, row=0, sticky='news', in_=self)
        vsb.grid(column=1, row=0, sticky='ns', in_=self)
        hsb.grid(column=0, row=1, sticky='ew', in_=self)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def bindWidgets(self):
        self.tree.bind('<Button-3>', self.call_popup)
        self.tree.bind('<Control-Insert>', self.clipboard)
        self.tree.bind('<Control-c>', self.clipboard)

    def sortby(self, col, descending): #column click sort
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]

        data.sort(reverse=descending)
        for i, item in enumerate(data):
            self.tree.move(item[1], '', i)

        # switch the heading so that it will sort in the opposite direction
        self.tree.heading(col,
            command=lambda col=col: self.sortby(col, int(not descending)))

    def fill_tree(self, _gloss):
        try: # py2/3 compatibility
            file=open(self.GLOSS, encoding="UTF-8").read().splitlines()
        except:
            file=open(self.GLOSS).read().splitlines()

        self.count=0

        for line in file:
            self.count+=1
            try:  # py2/3 compatibility
                line=line.decode('utf-8')
            except:
                pass

            row=line.split(';')
            row.insert(0, self.count)
            row[2]=row[2][1:] # remove space
            self.select=self.tree.insert('', 'end', values=row)

    def clear_tree(self):
        x = self.tree.get_children()
        for item in x: self.tree.delete(item)

    def reload_tree(self):
        self.clear_tree()
        self.fill_tree(self.GLOSS)

    def treeSetFocus(self):
        print("%5d"%self.count, self.GLOSS.split('/')[-1])
        if self.tree.focus()!="": return

        if self.count:
            self.tree.selection_set('I001')
            self.tree.focus('I001')
            self.tree.focus_set()

    def toggle_display(self, *args):
        if self.visible: self.pack_forget()
        else: self.pack(expand=NO, side=TOP, fill=BOTH, anchor=N)
        self.visible = not self.visible

    def clipboard(self, event):
        # index=nb.index(nb.select())
        # obj=glist[index]
        sel=self.tree.item(self.tree.focus())
        val=sel['values']
        root.clipboard_clear()
        root.clipboard_append(val[2])
        print("Copied to clipboard")

    def make_popup(self):
        popup = Menu(self, tearoff=0)
        popup.add_command(label="Edit", command=None)
        popup.add_command(label="Open Directory", accelerator="Ctrl+o", command=None)
        popup.add_command(label="Open Gloss", command=None)
        popup.add_separator()
        popup.add_command(label="Reload", command=None)
        self.popup=popup

    def call_popup(self, event):
        global POP_SELECT
        ex=event.x_root
        ey=event.y_root
        offset=19*4
        self.popup.tk_popup(ex,ey)
        POP_SELECT=ttk.Treeview.identify(self.tree, component='item', x=ex, y=ey-offset)
        self.tree.selection_set(POP_SELECT)
        self.tree.focus(POP_SELECT)
        self.tree.focus_set()

class GUI(Frame):
    def __init__(self, parent=None):
        Frame.__init__(self, parent)
        self.visible = True
        self.glist=[]
        self.makeWidgets()
        self.bindWidgets()
        self.pack(expand=NO, fill=X, side=TOP)

    def makeWidgets(self):
        # searchbox
        ttksbox.entrystyle()
        self.sbox=ttksbox.ttk.Entry(self, style="Search.entry", width=20)
        self.sbox.insert(0, "Search")

        self.found_status=Label(self) #TODO: GUI status display

        var=IntVar() # TODO: autocopy to clipboard
        self.cbox_acopy = tk.Checkbutton(self, text="auto copy", command=None, variable=var)
        var.set(1)

        self.nb = ttk.Notebook()
        self.nb.enable_traversal()

        #packing
        self.sbox.pack(expand=NO, side=RIGHT, fill=X)
        self.cbox_acopy.pack(side=LEFT)
        self.nb.pack(expand=YES, fill=BOTH, side=BOTTOM)

    def bindWidgets(self):
        self.sbox.bind('<Control-c>', lambda e: self.sbox.delete(0,END))
        self.sbox.bind('<Control-g>', lambda e: self.sbox.delete(0,END))

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
        nav.sbox.focus()
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
        sbox_text=self.sbox.get()
        if sbox_text:
            sbox_next_search();
        else: # if empty get from clipboard
            clip_text=root.clipboard_get()
            if clip_text:
                self.sbox.insert(0, clip_text)

    def toggle_display(self, *args):
        if self.visible: self.pack_forget()
        else: self.pack(expand=NO, fill=X, side=TOP)
        self.visible = not self.visible

    def switch_tab(self, *event):
        tab=int(event[0].char)-1
        obj=self.glist[tab]
        # BUG: object focus after tabswitch not working properly
        # print(index, tab, tab_info[tab])
        self.nb.select(tab)
        obj.treeSetFocus()

    # TODO: add the decorator in all this stuffs :D
    def open_gloss(self, *events):
        index=self.nb.index(self.nb.select())
        obj=self.glist[index]
        os.system("setsid %s %s"%("leafpad", obj.GLOSS))

    def open_dir(self, *events):
        index=self.nb.index(self.nb.select())
        obj=self.glist[index]
        os.system("setsid %s %s"%(FILEMGR, obj.GLOSS))

    def reload_gloss(self, *events):
        index=self.nb.index(self.nb.select())
        obj=self.glist[index]
        obj.reload_tree()
        print("Reload %s"%obj.GLOSS)

    def load_files(self):
        for i, file in enumerate(os.listdir(PATH_GLOSS)):
            if not file[-4:] in FILE_TYPES: continue
            obj=BrowseList(PATH_GLOSS+file)
            self.nb.add(obj, text=file, padding=3)
            self.glist.append(obj)
            if i < 10:
                root.bind('<Alt-KeyPress-%d>'%(i+1), self.switch_tab)

        return self.glist

def key_press(event):
    typed=event.char
    if not typed.isalpha(): return
    nav.sbox.delete(0, END)
    nav.sbox.insert(0, typed)
    nav.sbox.focus()
    root.unbind('<Key>')

def sbox_next_search(*args):
    global word
    word=nav.sbox.get().lower().strip()

    global lang
    if word.isalpha(): lang=1;
    else: lang=2

    for i, obj in enumerate(nav.glist):
        if search_tree(i, obj, word):
            nav.sbox.select_range(0, END)
            return

    print("\"%s\" not found"%word)

    #generate_near_words
    for i, obj in enumerate(nav.glist):
        print(find_near(i, obj, word));

    global ADD_LOCK
    ADD_LOCK=False

def search_tree(tab, obj, word):
    list = obj.tree.get_children()
    for item in list:
        sel=obj.tree.item(item)
        val=sel['values'][lang]
        if val==word:
            nav.nb.select(tab)
            obj.tree.selection_set(item)
            obj.tree.focus(item)
            obj.tree.focus_set()
            root.update()
            obj.tree.yview(int(item[1:], 16)-1)
            return True
    return False

def find_near(tab, obj, word):
    #get the maximum matched string?
    match = 1000 #leser-the-better
    holder = []
    list = obj.tree.get_children()
    for item in list:
        sel=obj.tree.item(item)
        val=sel['values'][lang]
        #print(val.__doc__)
        #print(word.__doc__)
        dis = lev_dis(word, val)
        if(dis < match):
            match = dis
            holder = []
            holder.append(val+str(match))
        elif(dis == match):
            holder.append(val+str(match))
    return holder
#End find_near

def lev_dis(seq1,seq2):
    oneago = None
    thisrow = list(range(1, len(seq2) + 1))
    thisrow.append(0)
    for x in range(len(seq1)):
        twoago, oneago, thisrow = oneago, thisrow, [0] * len(seq2) + [x + 1]
        for y in range(len(seq2)):
            delcost = oneago[y] + 1
            addcost = thisrow[y - 1] + 1
            subcost = oneago[y - 1] + (seq1[x] != seq2[y])
            thisrow[y] = min(delcost, addcost, subcost)
    return thisrow[len(seq2) - 1]
#End lev_dis

def add_to_list(*args):
    global ADD_LOCK, word
    if ADD_LOCK:
        print("World already Exist, only edit possible")
        return 1;

    DIRTY=True
    ADD_LOCK=True
    anubad=askstring("Entry", "anubad: %s"%word)
    if not anubad: return

    i=nav.nb.index(nav.nb.select())
    obj=nav.glist[i]

    obj.count+=1
    row = [ obj.count, word, anubad ]
    select=obj.tree.insert('', 'end', values=row)

    # TODO: make class method do view
    obj.tree.selection_set(select)
    obj.tree.focus(select)
    obj.tree.focus_set()
    obj.tree.yview(int(select[1:], 16)-1)
    fp=open(obj.GLOSS, 'a').write("\n"+word+"; "+anubad)
    print(fp)

def cli_mode(list):
    file=open(GLOSS).read()
    print("CLI-mode Currenly Disabled")
    # for word in list:
    #     found=file.find(word)
    #     if found == -1:
    #         print("%s Not Found"%word)
    #         break
    #     for i, char in enumerate(file[found:]):
    #         if char=='\n': break
    #         print(char)
    #     #os.system("echo %s | xclip -i"%file[found:found+i])

    #     print()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        cli_mode(sys.argv[1:])
        exit()

    root=Tk()
    root.title("anubad")

    nav=GUI()
    nav.load_files()
    nav.glist[0].treeSetFocus()

    root.bind('<Key-Escape>', lambda event: quit())
    root.bind('<Control-d>', lambda event: quit())

    root.mainloop()
