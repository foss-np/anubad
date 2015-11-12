#!/usr/bin/env python3

import argparse

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

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
        # _menu.popup(None, None, lambda w, x: self.position_menu(_menu, self), self, 3, time)


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
    global PATH_PLUGINS
    PATH_PLUGINS = PWD + PATH_PLUGINS
    if not os.path.isdir(PATH_PLUGINS): return
    if PATH_PLUGINS == PWD: return
    sys.path.append(PATH_PLUGINS)


    parent.plugins = dict()
    for file_name in os.listdir(PATH_PLUGINS):
        if file_name[-3:] not in ".py": continue
        namespace = importlib.__import__(file_name[:-3])
        if namespace.plugin_main(parent, PWD):
            print("plugin:", file_name, file=sys.stderr)
            parent.plugins[file_name[:-3]] = namespace


def argparser():
    parser = argparse.ArgumentParser(description="anubad")
    parser.add_argument(
        "-q", "--quick",
        action  = "store_true",
        default = False,
        help    = "Disable plugins loading")

    return parser.parse_args()


if __name__ == '__main__':
    args = argparser()

    root = main()
    root.set_title(PKG_NAME)
    root.visible = True
    root.toolbar.b_About.connect("clicked", about_dialog)

    if not args.quick:
        load_plugins(root)

    tray = TrayIcon(root)
    Gtk.main()
