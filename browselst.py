#!/usr/bin/python
# -*- coding: utf-8 -*-
# ^^^ needed for py2

try: #py2/3 compatibiliy
    from tkinter import *
    import tkinter.ttk as ttk
except:
    from Tkinter import *
    import ttk

#  ____                               _     _     _
# | __ ) _ __ _____      _____  ___  | |   (_)___| |_
# |  _ \| '__/ _ \ \ /\ / / __|/ _ \ | |   | / __| __|
# | |_) | | | (_) \ V  V /\__ \  __/ | |___| \__ \ |_
# |____/|_|  \___/ \_/\_/ |___/\___| |_____|_|___/\__|

cols = ["#", "en", "ne"]

col_attrib = [
   #["id", "label", min-width, width, stretch, !show],
    ["#", "#", 50, 50, 0, False],
    ["en", "English", 90, 90, 1, False],
    ["ne", "नेपाली", 250, 170, 1, False]
]

class BrowseList(Frame):
    """
    Create the tkinter table using ttk.Treeview

    >>> obj = BrowseList()
    """

    def __init__(self, parent=None, gloss=None):
        Frame.__init__(self, parent)
        self.popup = None
        self.copy_smart = False
        self.makeWidgets(cols, col_attrib)
        self.bindWidgets()
        self.GLOSS = gloss
        self.h1 = def_font[:2] + ["bold"]
        if self.GLOSS:
            # avoid utf-8 print in terminal
            # print("loading", self.GLOSS.split('/')[-1])
            self.fill_tree(self.GLOSS)

        self.pack(expand=YES, side=TOP, fill=BOTH, anchor=N)


    def makeWidgets(self, _c, _a):
        # a treeview
        self.tree = ttk.Treeview(self, show="headings", columns=_c)
        self.tree.config(selectmode="browse")

        # adding header
        for a in _a:
            if a[-1]: continue
            self.tree.heading(a[0], text=a[1])
            self.tree.heading(a[0], command=lambda A=a[0]: self.sortby(A, 0))
            self.tree.column(a[0], minwidth=a[2], width=a[3], stretch=a[4])

        # adding scrollbar
        vsb = Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # focus
        vsb.config(takefocus=0)
        hsb.config(takefocus=0)

        # packing to grid
        self.tree.grid(column=0, row=0, sticky='news', in_=self)
        vsb.grid(column=1, row=0, sticky='ns', in_=self)
        hsb.grid(column=0, row=1, sticky='ew', in_=self)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def bindWidgets(self):
        self.tree.bind('<Button-3>', self.call_popup)
        self.tree.bind('<Control-Insert>', self.clipboard)
        self.tree.bind('<Control-c>', self.clipboard_smart)

    def sortby(self, c, descending): #column click sort
        data = [(self.tree.set(n, c), n) for n in self.tree.get_children('')]

        data.sort(reverse=descending)
        for i, item in enumerate(data):
            self.tree.move(item[1], '', i)

        # switch the heading so that it will sort in the opposite direction
        self.tree.heading(c,
            command=lambda C=c: self.sortby(C, int(not descending)))

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
                # TODO: open leafpad automatically with the current error line
                exit()

            self.select = self.tree.insert('', 'end', values=row, tag="npfont")

        self.tree.tag_configure("npfont", font=def_font)

    def clear_tree(self):
        x = self.tree.get_children()
        for item in x: self.tree.delete(item)

    def reload_tree(self):
        self.clear_tree()
        self.fill_tree(self.GLOSS)

    def treeSetFocus(self):
        if not self.count: return # if no data

        if self.tree.focus() == "":
            #print("%5d"%self.count, self.GLOSS.split('/')[-1])
            self.tree.selection_set('I001')
            self.tree.focus('I001')

        self.tree.focus_set()

    def toggle_display(self, *args):
        if self.visible: self.pack_forget()
        else: self.pack(expand=NO, side=TOP, fill=BOTH, anchor=N)
        self.visible = not self.visible

    def clipboard(self, *event):
        # index = nb.index(nb.select())
        # obj = glist[index]
        sel = self.tree.item(self.tree.focus())
        val = sel['values']
        self.master.clipboard_clear()
        self.master.clipboard_append(val[2])
        print("Copied to clipboard")

    def clipboard_smart(self, event):
        try: # seem like in there is no var defined
            old_val = root.clipboard_get()
        except:
            old_val = ""

        sel = self.tree.item(self.tree.focus())
        val = sel['values']
        new_val = val[2].split(',')[0]

        self.master.clipboard_clear()

        if old_val == new_val:
            self.copy_smart = True
            self.master.clipboard_append(val[2])
        else:
            self.master.clipboard_append(new_val)

        print("smart clipboard")

    def make_popup(self, ID, word):
        popup = Menu(self, tearoff=0)
        popup.add_command(label=ID + ' : ' + word, state=DISABLED, font=self.h1)
        popup.add_command(label="Edit", command=lambda: open_gloss())
        popup.add_command(label="Open Gloss", command=lambda: open_gloss())
        popup.add_separator()
        popup.add_command(label="Search online", command=lambda: web_search(word))
        return popup

    def get_ID_below_mouse(self, event):
        HEIGHT = 19
        offset = HEIGHT * 15
        ex, ey = event.x_root, event.y_root - offset
        ID = ttk.Treeview.identify(self.tree, component='item', x=ex, y=ey)

        self.tree.selection_set(ID)
        self.tree.focus(ID)
        self.tree.focus_set()

        return ID

    def call_popup(self, event):
        ID = self.get_ID_below_mouse(event)
        word = self.tree.item(ID)['values'][1]
        popup = self.make_popup(ID, word)
        popup.tk_popup(event.x_root, event.y_root)
        del popup


def open_gloss():
    print("dummy %s.open_gloss()"%__name__)


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
