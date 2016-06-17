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

from gi.repository import Gtk
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
            self.app.activate()
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
    def __init__(self, opts):
        Gtk.Application.__init__(
            self,
            application_id = __PKG_ID__,
            flags = Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
        )

        self.opts = opts
        self.home = None


    def do_startup(self):
        Gtk.Application.do_startup(self)

        self.rc = config.main(PWD)
        apply_rc_changes(self.rc, self.opts)

        verify_mime(self.rc)
        core.load_from_config(self.rc)

        self.plugins = { k: v for k, v in scan_plugins(self.rc) }
        self.pixbuf_logo = GdkPixbuf.Pixbuf.new_from_file(PWD + '../assets/anubad.png')


    def do_activate(self):
        if self.home == None:
            self.home = self.create_home_window()
            load_plugins(self, self.plugins)
            if self.rc.preferences['hide-on-startup']: return

        self.home.show()
        self.home.parse_geometry(self.rc.gui['geometry'])
        self.home.present()


    def do_shutdown(self):
        if self.home and self.rc.preferences['enable-history-file']:
            print("shutdown: update history")
            fp = open(os.path.expanduser(config.FILE_HIST), mode='w+')
            fp.write('\n'.join(self.home.search_entry.HISTORY))
            fp.close()
        self.quit()


    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        argv = command_line.get_arguments()
        if len(argv) == 0:
            self.activate()
            return 0

        return 0


    def create_home_window(self):
        home = ui.home.Home(core, self.rc)
        self.add_window(home)
        home.set_icon(self.pixbuf_logo)
        home.set_title(__PKG_NAME__)
        home.connect('delete-event', lambda *a: self.quit())

        self.add_about_to_toolbar(home.toolbar)
        home.engines.append((lambda q: q[0] == '>', self.commander.gui_adaptor))

        if self.rc.preferences['show-on-taskbar']    : home.set_skip_taskbar_hint(True)
        if self.rc.preferences['show-on-system-tray']:
            self.tray = TrayIcon(self, self.rc.preferences['hide-on-startup'])
        if self.rc.preferences['enable-history-file']:
            home.search_entry.HISTORY += open(
                os.path.expanduser(config.FILE_HIST),
                encoding = "UTF-8"
            ).read().splitlines()
            home.search_entry.CURRENT = len(home.search_entry.HISTORY)

        return home


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


def apply_rc_changes(rc, opts):
    rc.core['no-thread']                   = opts.nothread
    rc.preferences['enable-plugins']      *= not opts.noplugins
    rc.preferences['hide-on-startup']      = opts.hide
    rc.preferences['show-on-system-tray'] *= not opts.notray
    rc.preferences['enable-history-file'] *= not opts.nohistfile
    if rc.preferences['show-on-system-tray']:
        rc.preferences['show-on-taskbar'] *= opts.notaskbar


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
        "--hide",
        action  = "store_true",
        default = False,
        help    = "Hide on startup")

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

    parser.add_argument(
        "--nothread",
        action  = "store_true",
        default = False,
        help    = "Don't thread application")

    return parser


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    parser = create_arg_parser()
    opts, unknown = parser.parse_known_args()
    app = App(opts)
    app.run(unknown)
