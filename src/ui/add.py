#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class Add(Gtk.Window):
    def __init__(self, parent=None, l1="", l2=""):
        Gtk.Window.__init__(self, title="Add gloss")
        self.parent = parent
        self.track_FONT = set()
        self.l1 = l1
        self.l2 = l2

        self.makeWidgets()
        if parent: self.cb_file_add()

        self.connect('key_press_event', lambda w, e: self.key_binds(w, e))
        self.show_all()


    def makeWidgets(self):
        layout = Gtk.Grid()
        self.add(layout)
        layout.set_row_spacing(5)
        layout.set_column_spacing(5)

        # self.font_button = Gtk.FontButton()
        # layout.add(self.font_button)
        # self.font_button.set_font_name(def_FONT)
        # self.font_button.connect('font-set', self._change_font)

        label = Gtk.Label()
        layout.attach(label, 0, 0, 1, 1)
        label.set_markup("<b>lang_1</b>")

        self.lang1 = Gtk.Entry()
        layout.attach(self.lang1, 1, 0, 1, 1)
        self.track_FONT.add(self.lang1)
        self.lang1.set_text(self.l1)

        # TODO: don't process option
        # raw = method

        label = Gtk.Label()
        layout.attach(label, 0, 1, 1, 1)
        label.set_markup("<b>lang_2</b>")

        self.lang2 = Gtk.Entry()
        layout.attach(self.lang2, 1, 1, 1, 1)
        self.track_FONT.add(self.lang2)
        self.lang2.set_text(self.l2)

        label = Gtk.Label()
        layout.attach(label, 0, 2, 1, 1)
        label.set_markup("<b>file</b>")

        self.gloss_file = Gtk.ComboBoxText()
        layout.attach(self.gloss_file, 1, 2, 1, 1)

        layout.attach(self.makeWidgets_buttons(), 0, 3, 2, 1)


    def makeWidgets_buttons(self):
        layout = Gtk.HBox()

        self.icon_cancel = Gtk.Image.new_from_stock(Gtk.STOCK_CANCEL, Gtk.IconSize.BUTTON)
        self.icon_add = Gtk.Image.new_from_stock(Gtk.STOCK_ADD, Gtk.IconSize.BUTTON)

        self.b_cancel = Gtk.Button.new_with_label("Cancel")
        self.b_cancel.set_image(self.icon_cancel)

        layout.add(self.b_cancel)
        self.b_cancel.connect("clicked", lambda e: self.destroy())


        self.b_add = Gtk.Button.new_with_label("Add")
        # self.b_add = Gtk.Button.new_from_stock(Gtk.STOCK_ADD)
        self.b_add.set_image(self.icon_add)

        layout.add(self.b_add)
        self.b_add.connect("clicked", self._add_button)

        return layout


    def cb_file_add(self):
        for i in range(self.parent.notebook.get_n_pages()):
            obj = self.parent.notebook.get_nth_page(i)
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
        obj = self.parent.notebook.get_nth_page(t)
        fp = open(obj.SRC, 'a').write("\n" + '; '.join(row))
        count = obj.add_to_tree(row)
        row = [t, obj, count] + row

        # TODO: move this to main.py return destroy signal
        # self.parent.items_FOUND.clear()
        # self.parent.items_FOUND.append(row)
        # self.parent._view_items([0])
        self.destroy()
        # return t, row


    def key_binds(self, widget, event):
        # print(event.keyval)
        if event.keyval == 65307: self.destroy() # Esc


def main():
    root = Add()
    root.connect('delete-event', Gtk.main_quit)
    return root


if __name__ == '__main__':
    main().destroy = Gtk.main_quit
    Gtk.main()
