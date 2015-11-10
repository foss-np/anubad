#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class Settings(Gtk.Window):
    # TODO: Singleton
    def __init__(self, parent=None):
        Gtk.Window.__init__(self, title="Settings")
        self.parent = parent

        self.makeWidgets()

        self.connect('key_press_event', lambda w, e: self.key_binds(w, e))
        self.show_all()

    def makeWidgets(self):
        layout = Gtk.Grid()
        self.add(layout)
        layout.set_row_spacing(5)
        layout.set_column_spacing(5)

        label = Gtk.Label()
        layout.attach(label, 0, 1, 1, 1)
        label.set_markup("<b>Font</b>")

        self.font_button = Gtk.FontButton()
        layout.attach(self.font_button, 1, 1, 1, 1)
        self.font_button.set_font_name(def_FONT)
        self.font_button.connect('font-set', self._change_font)

        layout.attach(self.makeWidgets_behavious(), 0, 2, 2, 1)
        layout.attach(self.makeWidgets_buttons(), 0, 3, 2, 1)

        return layout


    def _change_font(self, widget):
        f_obj = widget.get_font_desc()
        for obj in self.parent.track_FONT:
            obj.modify_font(f_obj)
            # obj.override_font(f_obj)

    def makeWidgets_behavious(self):
        bar = Gtk.Toolbar()
        ## Auto Transliterate Button
        bar.t_Trans = Gtk.ToggleToolButton(icon_name=Gtk.STOCK_CONVERT)
        bar.add(bar.t_Trans)
        bar.t_Trans.set_active(True)
        ##
        ## Spell-check Toggle Button
        bar.t_Spell = Gtk.ToggleToolButton(icon_name=Gtk.STOCK_SPELL_CHECK)
        bar.add(bar.t_Spell)
        bar.t_Spell.set_active(True)
        ##
        return bar

    def makeWidgets_buttons(self):
        layout = Gtk.HBox()
        # layout.set_row_spacing(5)
        # layout.set_column_spacing(5)

        self.b_cancel = Gtk.Button.new_from_stock(Gtk.STOCK_CANCEL)
        layout.add(self.b_cancel)
        self.b_cancel.connect("clicked", lambda e: self.destroy())

        self.b_apply = Gtk.Button.new_from_stock(Gtk.STOCK_APPLY)
        layout.add(self.b_apply)
        self.b_apply.connect("clicked", lambda e: self.destroy())

        self.b_ok = Gtk.Button.new_from_stock(Gtk.STOCK_REFRESH)
        layout.add(self.b_ok)

        return layout


    def makeWidgets_settings(self):
        layout = Gtk.HBox()

        self.font_button = Gtk.FontButton()
        layout.add(self.font_button)
        self.font_button.set_font_name(def_FONT)
        self.font_button.connect('font-set', self._change_font)

        # SHOW HIDE GLOSS
        # toolbar.insert(Gtk.ToolButton.new_from_stock(Gtk.STOCK_GOTO_TOP), 0)
        # toolbar.insert(Gtk.ToolButton.new_from_stock(Gtk.STOCK_GOTO_BOTTOM), 0)
        # layout.add(Gtk.ToolButton.new_from_stock(Gtk.STOCK_CLOSE))
        # layout.add(Gtk.ToolButton.new_from_stock(Gtk.STOCK_APPLY))
        return layout


    def _apply_click(self, widget):
        f_obj = widget.get_font_desc()
        self.viewer.textview.modify_font(f_obj)
        ff, fs = f_obj.get_family(), int(f_obj.get_size()/1000)
        font = ff + ' ' + str(fs)
        # conf = open("mysettings.conf").read()
        # global def_FONT
        # nconf = conf.replace(def_FONT, font)
        # open("mysettings.conf", 'w').write(nconf)
        # def_FONT = font


    def cb_file_add(self):
        for obj in self.parent.TAB_LST:
            *a, label = obj.SRC.split('/')
            self.gloss_file.append_text(label)

            self.gloss_file.set_active(self.parent.notebook.get_current_page())


    def _add_button(self, widget=None):
        pass


    def key_binds(self, widget, event):
        # print(event.keyval)
        if event.keyval == 65307: self.destroy() # Esc


def main():
    root = Settings()
    root.connect('delete-event', Gtk.main_quit)
    return root


if __name__ == '__main__':
    from gi.repository import Pango
    exec(open("gsettings.conf").read())
    FONT_obj = Pango.font_description_from_string(def_FONT)
    main().destroy = Gtk.main_quit
    Gtk.main()
