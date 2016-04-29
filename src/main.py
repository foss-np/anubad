#!/usr/bin/env python3

import argparse
import signal

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from main import *

PKG_NAME = "anubad - अनुवाद"

class TrayIcon(Gtk.StatusIcon):
    def __init__(self, parent=None):
        Gtk.StatusIcon.__init__(self)
        self.parent = parent
        self.do_activate()

    def do_activate (self):
        self.set_from_stock(Gtk.STOCK_HOME)
        self.connect("activate", self.trayicon_activate)
        self.connect("popup_menu", self.trayicon_popup)

        self.set_title("anubad")
        self.set_name("anubad glossary browser")
        self.set_tooltip_text("anubad")
        self.set_has_tooltip(True)
        self.set_visible(True)


    def trayicon_activate(self, widget):
        if self.parent.visible == False:
            self.parent.visible = True
            self.parent.show()
            return

        self.parent.visible = False
        self.parent.hide()


    def trayicon_quit(self, widget):
        Gtk.main_quit()


    def trayicon_popup(self, widget, button, time, data = None):
        _menu = Gtk.Menu()

        _toggle = Gtk.MenuItem("Show / Hide")
        _toggle.connect("activate", self.trayicon_activate)
        _menu.append(_toggle)

        menuitem_quit = Gtk.MenuItem("Quit")
        menuitem_quit.connect("activate", self.trayicon_quit)
        _menu.append(menuitem_quit)

        _menu.show_all()
        _menu.popup(None, None, lambda w, x: self.position_menu(_menu, self), self, 3, time)


    def do_deactivate(self):
        self.staticon.set_visible(False)
        del self.staticon


def about_dialog(widget):
    aboutdialog = Gtk.AboutDialog()
    # aboutdialog.set_default_size(200, 800) # BUG: Not WORKING
    aboutdialog.set_logo_icon_name(Gtk.STOCK_ABOUT)
    aboutdialog.set_program_name(PKG_NAME)
    aboutdialog.set_comments("\nTranslation Glossary\n")
    aboutdialog.set_website("https://foss-np.github.io/anubad/")
    aboutdialog.set_website_label("Web Version")
    aboutdialog.set_authors(open(PWD + '../AUTHORS').read().splitlines())
    aboutdialog.set_license(open(PWD + '../LICENSE').read())
    aboutdialog.run()
    aboutdialog.destroy()


def load_plugins(parent):
    PATH_PLUGINS = PWD + root.rc.core['plugins']

    if not os.path.isdir(PATH_PLUGINS): return
    if PATH_PLUGINS == PWD: return
    sys.path.append(PATH_PLUGINS)

    parent.plugins = dict()
    for file_name in os.listdir(PATH_PLUGINS):
        if file_name[-3:] not in ".py": continue
        namespace = importlib.__import__(file_name[:-3])
        try:
            if namespace.plugin_main(parent, PWD):
                print("plugin:", file_name, file=sys.stderr)
                parent.plugins[file_name[:-3]] = namespace
        except Exception as e:
            print(e, file=sys.stderr)


def argparser():
    """
    anubad [OPTIONS] [SOURCE]:[TARGETS] [TEXT]
    $ anubad en:np test
    $ anubad :np test
    $ anubad -q
    """
    parser = argparse.ArgumentParser(description="anubad")
    parser.add_argument(
        "-q", "--quick",
        action  = "store_true",
        default = False,
        help    = "Disable plugins loading")

    return parser.parse_args()


def InitSignal(gui):
    def signal_action(signal):
        if signal is 1:
            print("Caught signal SIGHUP(1)")
        elif signal is 2:
            print("Caught signal SIGINT(2)")
        elif signal is 15:
            print("Caught signal SIGTERM(15)")
        # gui.cleanup()
        # TODO clean quit
        Gtk.main_quit()

    def idle_handler(*args):
        print("Python signal handler activated.")
        GLib.idle_add(signal_action, priority=GLib.PRIORITY_HIGH)

    def handler(*args):
        print("GLib signal handler activated.")
        signal_action(args[0])

    def install_glib_handler(sig):
        unix_signal_add = None

        if hasattr(GLib, "unix_signal_add"):
            unix_signal_add = GLib.unix_signal_add
        elif hasattr(GLib, "unix_signal_add_full"):
            unix_signal_add = GLib.unix_signal_add_full

        if unix_signal_add:
            print("Register GLib signal handler: %r" % sig)
            unix_signal_add(GLib.PRIORITY_HIGH, sig, handler, sig)
        else:
            print("Can't install GLib signal handler, too old gi.")

    SIGS = [getattr(signal, s, None) for s in "SIGINT SIGTERM SIGHUP".split()]
    for sig in filter(None, SIGS):
        print("Register Python signal handler: %r" % sig)
        signal.signal(sig, idle_handler)
        GLib.idle_add(install_glib_handler, sig, priority=GLib.PRIORITY_HIGH)


if __name__ == '__main__':
    args = argparser()

    root = main()
    root.set_title(PKG_NAME)
    root.visible = True
    root.toolbar.b_About.connect("clicked", about_dialog)

    if not args.quick:
        load_plugins(root)

    tray = TrayIcon(root)
    InitSignal(root)
    Gtk.main()
