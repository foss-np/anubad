#!/usr/bin/python3
#^^^ not using env for process name

__PKG_ID__   = "apps.anubad"
__PKG_NAME__ = "anubad - अनुवाद"
__PKG_DESC__ = "A Glossary Browser"

import os, sys
import argparse
import signal
import traceback
import importlib

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk
from gi.repository import GLib, Gio
from gi.repository import GdkPixbuf

import config
import core
import ui.home
PWD = ui.home.PWD

class TrayIcon(Gtk.StatusIcon):
    def __init__(self, app, visible):
        Gtk.StatusIcon.__init__(self)
        self.app = app
        self.visible = visible
        self.makeWidget()
        self.connect("activate", self.toggle_visibility)
        self.connect("popup_menu", self.on_secondary_click)


    def makeWidget(self):
        self.set_from_pixbuf(self.app.pixbuf_logo)
        self.set_title(__PKG_NAME__)
        self.set_name(__PKG_ID__ + ".tray")
        self.set_tooltip_text(__PKG_DESC__)
        self.set_has_tooltip(True)
        self.set_visible(True)


    def toggle_visibility(self, widget):
        self.visible = not self.visible
        if self.visible:
            self.app.home.show()
            self.app.home.parse_geometry(self.app.home.rc.gui['geometry'])
            return

        self.app.home.hide()


    def on_secondary_click(self, widget, button, time):
        menu = Gtk.Menu()

        menuitem_visibility = Gtk.MenuItem("Show / Hide")
        menuitem_visibility.connect("activate", self.toggle_visibility)
        menu.append(menuitem_visibility)

        menuitem_notify = Gtk.MenuItem("Disable Notification")
        # menuitem_toggle.connect("activate", self.toggle_notify)
        menu.append(menuitem_notify)

        menuitem_quit = Gtk.MenuItem("Quit")
        menuitem_quit.connect("activate", lambda *a: self.app.quit())
        menu.append(menuitem_quit)

        menu.show_all()
        menu.popup(None, None, None, self, 3, time)


class App(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(
            self,
            application_id = __PKG_ID__,
            flags = Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
        )

        self.home = None


    def do_startup(self):
        print("do_startup")
        Gtk.Application.do_startup(self)

        rc = config.main(PWD)
        parser = create_arg_parser()
        argv, unknown = parser.parse_known_args()
        apply_args(rc, argv)

        verify_mime(rc)
        core.load_from_config(rc)

        self.plugins = { k: v for k, v in scan_plugins(rc) }

        self.pixbuf_logo = GdkPixbuf.Pixbuf.new_from_file(PWD + '../assets/anubad.png')

        ## Home window
        self.home = ui.home.main(core, rc)
        self.add_window(self.home)
        self.home.set_icon(self.pixbuf_logo)
        self.home.set_title(__PKG_NAME__)
        self.home.connect('delete-event', lambda *a: self.quit())
        self.add_about_to_toolbar(self.home.toolbar)

        load_plugins(self, self.plugins)

        # if rc.preferences['show-on-taskbar']    : self.home.set_skip_taskbar_hint(True)
        if rc.preferences['show-on-system-tray']: self.tray = TrayIcon(self, rc.preferences['hide-on-startup'])
        if rc.preferences['enable-history-file']:
            self.home.search_entry.HISTORY += open(
                os.path.expanduser(config.FILE_HIST),
                encoding = "UTF-8"
            ).read().splitlines()
            self.home.search_entry.CURRENT = len(self.home.search_entry.HISTORY)


    def do_activate(self):
        self.home.show()
        self.home.parse_geometry(self.home.rc.gui['geometry'])
        self.home.present()


    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        arguments = command_line.get_arguments()
        if len(arguments) <= 1:
            self.activate()
            return 0

        if   "exit" == arguments[1]: self.quit()
        elif "quit" == arguments[1]: self.quit()
        return 0


    def insert_plugin_item_on_toolbar(self, widget):
        bar = self.home.toolbar
        if hasattr(bar, "s_PLUGINS"):
            i = bar.get_item_index(bar.s_PLUGINS)
        else:
            bar.s_PLUGINS = Gtk.SeparatorToolItem()
            i = bar.get_item_index(bar.s_END)
            bar.insert(bar.s_PLUGINS, i)
            bar.s_PLUGINS.show()

        bar.insert(widget, i+1)


    def add_about_to_toolbar(self, bar):
        bar.b_ABOUT = Gtk.ToolButton(icon_name=Gtk.STOCK_ABOUT)
        bar.add(bar.b_ABOUT)
        bar.b_ABOUT.show()
        bar.b_ABOUT.set_tooltip_markup("About")

        def about_dialog(widget):
            about = Gtk.AboutDialog(title="anubad", parent=self.home)
            about.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
            about.set_logo(self.pixbuf_logo)
            about.set_program_name(__PKG_NAME__)
            about.set_comments("\nTranslation Glossary\n")
            about.set_website("http://anubad.herokuapp.com")
            about.set_website_label("Web Version")
            about.set_authors(open(PWD + '../AUTHORS').read().splitlines())
            about.set_license(open(PWD + '../LICENSE').read())
            about.run()
            about.destroy()

        bar.b_ABOUT.connect("clicked", about_dialog)


def verify_mime(rc):
    for name, _type in rc.MIME_TYPES:
        if not rc.preferences['use-system-defaults']:
            if rc.apps[name]: continue
        desktopAppInfo = Gio.app_info_get_default_for_type(_type, 0)
        rc.apps[name] = desktopAppInfo.get_executable()


def apply_args(rc, argv):
    rc.preferences['enable-plugins']      *= not argv.noplugins
    rc.preferences['show-on-system-tray'] *= not argv.notray
    rc.preferences['enable-history-file'] *= not argv.nohistfile
    if rc.preferences['show-on-system-tray']:
        rc.preferences['show-on-taskbar'] *= argv.notaskbar


def scan_plugins(rc):
    if not rc.preferences['enable-plugins']: return
    path_plugins = PWD + rc.core['plugins']
    if not os.path.isdir(path_plugins): return
    if path_plugins == PWD: return
    sys.path.append(path_plugins)

    for file_name in os.listdir(path_plugins):
        if '#' in file_name: continue # just for ignoring backup files
        if file_name[-3:] not in ".py": continue
        namespace = importlib.__import__(file_name[:-3])
        yield file_name[:-3], namespace


def load_plugins(app, plugins):
    for i, (name, plug) in enumerate(plugins.items()):
        try:
            if plug.plugin_main(app, PWD):
                print("plugin:", name, file=sys.stderr)
        except Exception as e:
            traceback.print_exception(*sys.exc_info())


def create_arg_parser():
    parser = argparse.ArgumentParser(description="anubad")
    parser.add_argument(
        "--noplugins",
        action  = "store_true",
        default = False,
        help    = "Disable plugins loading")

    parser.add_argument(
        "--notray",
        action  = "store_true",
        default = False,
        help    = "Hide from notification tray")

    parser.add_argument(
        "--nohistfile",
        action  = "store_true",
        default = False,
        help    = "Disable history file")

    parser.add_argument(
        "--notaskbar",
        action  = "store_true",
        default = False,
        help    = "Hide from taskbar")

    return parser


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = App()
    app.run(sys.argv)
