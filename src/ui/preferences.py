#!/usr/bin/env python3

import os

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

class Settings(Gtk.Window):
    __instance__ = None

    def __new__(cls, *args, **kargs):
        """Override the __new__ method to make singleton"""
        if cls.__instance__ is None:
            cls.__instance__ = Gtk.Window.__new__(cls)
            cls.__instance__.singleton_init(*args, **kargs)
        return cls.__instance__


    def singleton_init(self, rc, parent=None):
        Gtk.Window.__init__(
            self,
            # parent=parent, # creates the warning
            application=parent.app if hasattr(parent, "app") else None,
            title="Settings"
        )

        self.parent = parent
        self.rc = rc

        self.set_transient_for(parent)

        self.makeWidgets()

        self.connect('key_release_event', self.key_binds)
        self.connect('delete-event', lambda *a: self.on_destroy(*a))

        self.set_border_width(10)
        self.set_default_size(250, 200)


    def makeWidgets(self):
        layout = Gtk.Grid()
        self.add(layout)
        layout.set_row_spacing(5)
        layout.set_column_spacing(5)

        label = Gtk.Label()
        layout.attach(label, left=0, top=1, width=1, height=1)
        label.set_markup("<b>Font</b>")

        self.font_button = Gtk.FontButton()
        layout.attach(self.font_button, left=1, top=1, width=1, height=1)
        self.font_button.set_font_name(self.rc.fonts['viewer'])
        self.font_button.connect('font-set', self._change_font)

        layout.attach(self.makeWidgets_behavious(), left=0, top=2, width=2, height=1)
        layout.attach(self.makeWidgets_default_apps(), left=0, top=3, width=2, height=1)
        layout.attach(self.makeWidgets_buttons(), left=0, top=4, width=2, height=1)


    def _change_font(self, widget):
        f_obj = widget.get_font_desc()
        for obj in self.parent.track_FONT:
            obj.modify_font(f_obj)
            # obj.override_font(f_obj)


    def makeWidgets_default_apps(self):
        layout = Gtk.VBox()
        # layout.set_hexpand(True)

        switch = Gtk.CheckButton(label="use system default")
        layout.add(switch)
        switch.set_active(self.rc.preferences['use-system-defaults'])
        switch.connect("toggled", self.toggle_system_default)

        grid = Gtk.Grid()
        layout.add(grid)
        grid.set_column_spacing(5)
        grid.set_row_spacing(5)

        self.appchooser_widget = []
        self.appchooser_block = grid
        rc_app = self.rc['apps'] if 'apps' in self.rc.sections() else {}
        for i, (name, _type) in enumerate(self.rc.MIME_TYPES):
            label = Gtk.Label(label=name, xalign=1)
            grid.attach(label, left=0, top=i, width=1, height=1)

            chooser = Gtk.AppChooserButton(content_type=_type)
            grid.attach(chooser, left=1, top=i, width=1, height=1)
            chooser.set_show_dialog_item(True)
            chooser.set_heading(name) # heading for show_dialog_item
            chooser.set_show_default_item(True)

            cfg = os.path.basename(rc_app.get(name, ''))
            index = 0
            for n, row in enumerate(chooser.get_model()):
                desktopAppInfo = row[0]
                if desktopAppInfo is None: continue
                exe = desktopAppInfo.get_executable()
                if cfg == os.path.basename(exe):
                    index = n
                    break

            chooser.signal = None
            if not self.rc.preferences['use-system-defaults']:
                chooser.set_active(index)
                chooser.signal = chooser.connect("changed", self._chooser_changed)

            chooser.selected_item = index
            self.appchooser_widget.append(chooser)

        if self.rc.preferences['use-system-defaults']:
            grid.set_sensitive(False)

        # print(selected.get_id())
        # print(selected.get_name())
        # print(selected.get_display_name())
        # print(selected.get_filename())
        # print(dir(selected))
        # treeIter = model.get_iter(0)
        # selected = model.get_value(treeIter, 0)
        # print(selected.get_display_name())
        # print(selected.get_description())
        # print(selected.get_executable())
        return layout


    def toggle_system_default(self, checkButton):
        state = checkButton.get_active()
        self.appchooser_block.set_sensitive(not state)
        for i, w in enumerate(self.appchooser_widget):
            if w.signal: w.disconnect(w.signal)
            if state: w.refresh()
            else: w.set_active(w.selected_item)
            w.signal = w.connect("changed", self._chooser_changed)


    def _chooser_changed(self, appchooserbutton):
        i = appchooserbutton.get_active()
        appchooserbutton.selected_item = i


    def makeWidgets_behavious(self):
        bar = Gtk.Toolbar()
        ## Auto Transliterate Button
        # bar.t_Trans = Gtk.ToggleToolButton(icon_name=Gtk.STOCK_CONVERT)
        # bar.add(bar.t_Trans)
        # bar.t_Trans.set_active(True)
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
        self.b_cancel.connect("clicked", lambda *a: self.on_destroy(*a))

        self.b_apply = Gtk.Button.new_from_stock(Gtk.STOCK_APPLY)
        layout.add(self.b_apply)
        self.b_apply.connect("clicked", lambda *a: self.on_destroy(*a))

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
        pass
        # f_obj = widget.get_font_desc()
        # self.viewer.textview.modify_font(f_obj)
        # ff, fs = f_obj.get_family(), int(f_obj.get_size()/1000)
        # font = ff + ' ' + str(fs)

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


    def on_destroy(self, event, *args):
        """Override the default handler for the delete-event signal"""
        self.hide()
        return True


    def key_binds(self, widget, event):
        # print(event.keyval)
        if event.keyval == 65307: self.on_destroy(event) # Esc


def main(rc):
    win = Settings(rc)
    win.set_position(Gtk.WindowPosition.CENTER)
    win.show_all()
    return win


def sample():
    import sys
    sys.path.append(sys.path[0]+'/../')

    import config
    from gi.repository import Pango

    root = main(config.main())

    # in isolation testing, make Esc quit Gtk mainloop
    root.on_destroy = Gtk.main_quit


if __name__ == '__main__':
    sample()
    Gtk.main()
