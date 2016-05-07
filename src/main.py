#!/usr/bin/python3
#^^^ not using env for process name

__PKG_ID__ = "apps.anubad"
__PKG_NAME__ = "anubad - अनुवाद"
__PKG_DESC__ = "A Glossary Browser"

import os, sys

import argparse
import signal
import importlib

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GLib, Gio
from gi.repository import GdkPixbuf

import config
import core
import ui.home
PWD = ui.home.PWD

SIGS = (
    getattr(signal, "SIGINT",  None),
    getattr(signal, "SIGHUP",  None),
    getattr(signal, "SIGTERM", None),
)

class App(Gtk.Application):
    def __init__(self, argv):
        Gtk.Application.__init__(
            self,
            application_id=__PKG_ID__,
        )
        self.argv = argv

        self.connect("startup", self.on_startup)
        self.connect("activate", self.on_activate)
        # self.connect("shutdown", self.on_shutdown)


    def on_startup(self, *args):
        rc = config.main(PWD)

        rc.core['interrupt'] *= not self.argv.nointerrupt
        if rc.core['interrupt']:
            self.handle_signals()

        ## load GUI
        # verify app
        for name, _type in rc.type_list:
            if not rc.preferences['use-system-defaults']:
                if rc.apps[name]: continue
            desktopAppInfo = Gio.app_info_get_default_for_type(_type, 0)
            rc.apps[name] = desktopAppInfo.get_executable()

        # logo
        self.pixbuf_logo = GdkPixbuf.Pixbuf.new_from_file(PWD + '../assets/anubad.ico')

        # scan plugins
        self.plugins = dict()
        rc.preferences['enable-plugins'] *= not self.argv.noplugins
        if rc.preferences['enable-plugins']:
            self.scan_plugins(rc)

        ## home window
        self.root = ui.home.main(core, rc, app=self)
        self.add_window(self.root)
        self.root.set_icon(self.pixbuf_logo)
        self.root.set_title(__PKG_NAME__)
        self.root.visible = True
        self.root.connect('delete-event', lambda *a: self.quit())
        self.add_about_to_toolbar(self.root.toolbar)

        # load plugins
        for name, plug in self.plugins.items():
            try:
                if plug.plugin_main(self, PWD):
                    print("plugin:", name, file=sys.stderr)
            except Exception as e:
                print(e, file=sys.stderr)

        # load system tray
        rc.preferences['show-in-system-tray'] *= not self.argv.notray
        if rc.preferences['show-in-system-tray']:
            self.tray = TrayIcon(self)


    def handle_signals(self):
        for sig in filter(None, SIGS):
            signal.signal( # idle_handler
                sig,
                lambda *a: GLib.idle_add(
                    self.signal_action,
                    priority=GLib.PRIORITY_HIGH
                )
            )
            GLib.idle_add(
                GLib.unix_signal_add,
                GLib.PRIORITY_HIGH,
                sig,
                lambda *a: self.signal_action(a[0]),
                sig
            )


    def on_activate(self, *args):
        self.root.show_all()
        self.root.parse_geometry(self.root.rc.gui['geometry'])
        self.root.present()
        self.root.grab_focus()


    def on_shutdown(self, app_obj):
        print("on_shutdown")
        # app_obj.quit()


    def add_about_to_toolbar(self, bar):
        bar.b_About = Gtk.ToolButton(icon_name=Gtk.STOCK_ABOUT)
        bar.add(bar.b_About)
        bar.b_About.set_tooltip_markup("More About Anubad")
        bar.b_About.connect("clicked", self.about_dialog)
        bar.b_About.show()


    def scan_plugins(self, rc):
        PATH_PLUGINS = PWD + rc.core['plugins']
        if not os.path.isdir(PATH_PLUGINS): return
        if PATH_PLUGINS == PWD: return
        sys.path.append(PATH_PLUGINS)

        for file_name in os.listdir(PATH_PLUGINS):
            if file_name[-3:] not in ".py": continue
            namespace = importlib.__import__(file_name[:-3])
            self.plugins[file_name[:-3]] = namespace


    def about_dialog(self, widget):
        self.about = Gtk.AboutDialog(title="anubad", parent=self.root)
        self.about.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        self.about.set_logo(self.pixbuf_logo)
        self.about.set_program_name(__PKG_NAME__)
        self.about.set_comments("\nTranslation Glossary\n")
        self.about.set_website("https://foss-np.github.io/anubad/")
        self.about.set_website_label("Web Version")
        self.about.set_authors(open(PWD + '../AUTHORS').read().splitlines())
        self.about.set_license(open(PWD + '../LICENSE').read())
        self.about.run()
        self.about.destroy()


    def signal_action(self, signal):
        if   signal is  1: print("Caught signal SIGHUP(1)")
        elif signal is  2: print("Caught signal SIGINT(2)")
        elif signal is 15: print("Caught signal SIGTERM(15)")
        self.quit()


class TrayIcon(Gtk.StatusIcon):
    def __init__(self, app=None):
        Gtk.StatusIcon.__init__(self)
        self.app = app
        self.makeWidget()
        self.connect("activate", self.toggle_visibility)
        self.connect("popup_menu", self.on_secondary_click)


    def makeWidget(self):
        self.set_from_pixbuf(self.app.pixbuf_logo)
        self.set_title(__PKG_NAME__)
        self.set_name("anubad.tray")
        self.set_tooltip_text(__PKG_DESC__)
        self.set_has_tooltip(True)
        self.set_visible(True)


    def toggle_visibility(self, widget):
        if self.app.root.visible == False:
            self.app.root.visible = True
            self.app.root.show()
            self.app.root.parse_geometry(self.app.root.rc.gui['geometry'])
            return

        self.app.root.visible = False
        self.app.root.hide()


    def on_secondary_click(self, widget, button, time):
        self.menu = Gtk.Menu()

        menuitem_visibility = Gtk.MenuItem("Show / Hide")
        menuitem_visibility.connect("activate", self.toggle_visibility)
        self.menu.append(menuitem_visibility)

        menuitem_notify = Gtk.MenuItem("Disable Notification")
        # menuitem_toggle.connect("activate", self.toggle_notify)
        self.menu.append(menuitem_notify)

        menuitem_quit = Gtk.MenuItem("Quit")
        menuitem_quit.connect("activate", lambda *a: self.app.quit())
        self.menu.append(menuitem_quit)

        self.menu.show_all()
        self.menu.popup(None, None, None, self, 3, time)


def argparser():
    """
    anubad [OPTIONS] [SOURCE]:[TARGETS] [TEXT]
    $ anubad en:np test
    $ anubad :np test
    """
    parser = argparse.ArgumentParser(description="anubad")
    parser.add_argument(
        "-p", "--noplugins",
        action  = "store_true",
        default = False,
        help    = "Disable plugins loading")

    parser.add_argument(
        "-t", "--notray",
        action  = "store_true",
        default = False,
        help    = "Disable tray")

    parser.add_argument(
        "-i", "--nointerrupt",
        action  = "store_true",
        default = False,
        help    = "Disable interrupt")

    argv = parser.parse_args()
    return argv


def main():
    argv = argparser()
    return App(argv)


if __name__ == '__main__':
    app = main()
    exit_status = app.run(None) #sys.argv)
    # app.run(None)
    print("exit_status:", exit_status)
    exit(exit_status)
