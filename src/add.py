#!/usr/bin/env python

from gi.repository import Gtk, Gdk, Pango

class Add(Gtk.Window):
    def __init__(self, parent=None, l1="", l2=""):
        Gtk.Window.__init__(self, title="Add gloss")
        self.parent = parent
        self.l1 = l1
        self.l2 = l2

        self.makeWidgets()
        if parent: self.cb_file_add()

        self.connect('key_press_event', lambda w, e: self.key_binds(w, e))
        self.show_all()

    def makeWidgets(self):
        layout = Gtk.Grid()
        layout.set_row_spacing(5)
        layout.set_column_spacing(5)

        self.add(layout)

        label = Gtk.Label()
        layout.attach(label, 0, 0, 1, 1)
        label.set_markup("<b>lang_1</b>")

        self.lang1 = Gtk.Entry()
        layout.attach(self.lang1, 1, 0, 1, 1)
        self.lang1.set_text(self.l1)
        # self.lang1.grab_focus()

        label = Gtk.Label()
        layout.attach(label, 0, 1, 1, 1)
        label.set_markup("<b>lang_2</b>")

        self.lang2 = Gtk.Entry()
        layout.attach(self.lang2, 1, 1, 1, 1)
        self.lang2.set_text(self.l2)

        label = Gtk.Label()
        layout.attach(label, 0, 2, 1, 1)
        label.set_markup("<b>file</b>")

        self.gloss_file = Gtk.ComboBoxText()
        layout.attach(self.gloss_file, 1, 2, 1, 1)

        self.button_cancel = Gtk.Button(label="Cancel")
        layout.attach(self.button_cancel, 0, 3, 1, 1)
        self.button_cancel.connect("clicked", lambda e: self.destroy())

        self.button_add = Gtk.Button(label="Add")
        layout.attach(self.button_add, 1, 3, 1, 1)
        self.button_add.connect("clicked", self._add_button)


    def cb_file_add(self):
        for obj in self.parent.TAB_LST:
            *a, label = obj.SRC.split('/')
            self.gloss_file.append_text(label)

            self.gloss_file.set_active(self.parent.notebook.get_current_page())


    def _add_button(self, widget=None):
        row = [ self.lang1.get_text().strip().lower() ]
        row.append(self.lang2.get_text().strip())

        if not (row[0] and row[1]):
            self.lang1.grab_focus()
            return

        t = self.gloss_file.get_active()
        obj = self.parent.TAB_LST[t]
        fp = open(obj.SRC, 'a').write("\n" + '; '.join(row))
        count = obj.add_to_tree(row)
        row = [count] + row

        # TODO: move this to main.py
        self.parent.viewer.parse(t, obj, row)
        self.parent.FOUND_ITEMS.clear()
        self.parent.FOUND_ITEMS.append(row)
        self.parent.suggestions.clear()
        self.parent.suggestions.append([1, row[2]])
        self.parent.VIEWED_ITEMS.clear()
        self.parent.VIEWED_ITEMS.add(0)
        self.parent.CURRENT_VIEW = 0
        self.destroy()
        # return t, row


    def key_binds(self, widget, event):
        # print(event.keyval)
        if event.keyval == 65307: self.destroy() # Esc
        elif Gdk.ModifierType.SHIFT_MASK & event.state:
            if event.keyval == 65293: # <enter> return
                self._add_button()


def main():
    root = Add()
    root.connect('delete-event', Gtk.main_quit)
    return root


if __name__ == '__main__':
    main().destroy = Gtk.main_quit
    Gtk.main()
