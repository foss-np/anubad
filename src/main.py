#!/usr/bin/env python3

import argparse
import signal

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GLib, Gio

from ui.home import *

__PKG_ID__ = "apps.anubad"
__PKG_NAME__ = "anubad - अनुवाद"
__PKG_DESC__ = "anubad glossary browser"

class App(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(
            self,
            application_id=__PKG_ID__,
        )
        self.plugins = dict()
        self.connect("startup", self.makeGUI)
        self.connect("activate", self.on_activate)

        SIGS = (
            getattr(signal, "SIGINT",  None),
            getattr(signal, "SIGHUP",  None),
            getattr(signal, "SIGTERM", None),
        )

        for sig in filter(None, SIGS):
            # print("Register Python signal handler: %r" % sig)
            signal.signal( # idle_handler
                sig,
                lambda *a: GLib.idle_add(
                    self.signal_action,
                    priority=GLib.PRIORITY_HIGH
                )
            )

            GLib.idle_add(
                self.install_glib_handler,
                sig,
                priority=GLib.PRIORITY_HIGH
            )


    def add_about_to_toolbar(self, bar):
        bar.b_About = Gtk.ToolButton(icon_name=Gtk.STOCK_ABOUT)
        bar.add(bar.b_About)
        bar.b_About.set_tooltip_markup("More About Anubad")
        bar.b_About.connect("clicked", self.about_dialog)
        bar.b_About.show()


    def makeGUI(self, *args):
        self.root = main(app=self)
        self.add_window(self.root)
        self.root.set_title(__PKG_NAME__)
        self.add_about_to_toolbar(self.root.toolbar)
        self.root.visible = True

        if not argv.quick:
            self.load_plugins()

        self.tray = TrayIcon( self)


    def on_activate(self, *args):
        self.root.show_all()
        self.root.present()


    def load_plugins(self):
        PATH_PLUGINS = PWD + self.root.rc.core['plugins']
        if not os.path.isdir(PATH_PLUGINS): return
        if PATH_PLUGINS == PWD: return
        sys.path.append(PATH_PLUGINS)

        for file_name in os.listdir(PATH_PLUGINS):
            if file_name[-3:] not in ".py": continue
            namespace = importlib.__import__(file_name[:-3])
            try:
                if namespace.plugin_main(self.root, PWD):
                    print("plugin:", file_name, file=sys.stderr)
                    self.plugins[file_name[:-3]] = namespace
            except Exception as e:
                print(e, file=sys.stderr)


    def about_dialog(self, widget):
        self.about = Gtk.AboutDialog(title="anubad", parent=self.root)
        self.about.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        self.about.set_logo_icon_name(Gtk.STOCK_ABOUT)
        self.about.set_program_name(__PKG_NAME__)
        self.about.set_comments("\nTranslation Glossary\n")
        self.about.set_website("https://foss-np.github.io/anubad/")
        self.about.set_website_label("Web Version")
        self.about.set_authors(open(PWD + '../AUTHORS').read().splitlines())
        self.about.set_license(open(PWD + '../LICENSE').read())
        self.about.run()
        self.about.destroy()


    def key_binds(self, widget, event):
        if event.keyval == 65307: Gtk.main_quit()


    def signal_action(self, signal):
        if   signal is  1: print("Caught signal SIGHUP(1)")
        elif signal is  2: print("Caught signal SIGINT(2)")
        elif signal is 15: print("Caught signal SIGTERM(15)")
        self.quit()


    def install_glib_handler(self, sig):
        unix_signal_add = None

        if hasattr(GLib, "unix_signal_add"):
            unix_signal_add = GLib.unix_signal_add
        elif hasattr(GLib, "unix_signal_add_full"):
            unix_signal_add = GLib.unix_signal_add_full

        if unix_signal_add:
            # print("Register GLib signal handler: %r" % sig)
            unix_signal_add(
                GLib.PRIORITY_HIGH,
                sig,
                lambda *a: self.signal_action(a[0]),
                sig
            )
        else:
            print("Can't install GLib signal handler, too old gi.")


class TrayIcon(Gtk.StatusIcon):
    def __init__(self, app=None):
        Gtk.StatusIcon.__init__(self)
        self.app = app
        self.makeWidget()
        self.connect("activate", self.toggle_visibility)
        self.connect("popup_menu", self._popup)


    def makeWidget(self):
        self.set_from_stock(Gtk.STOCK_HOME)
        self.set_title("anubad")
        self.set_name(__PKG_NAME__)
        self.set_tooltip_text(__PKG_DESC__)
        self.set_has_tooltip(True)
        self.set_visible(True)


    def toggle_visibility(self, widget):
        if self.app.root.visible == False:
            self.app.root.visible = True
            self.app.root.show()
            return

        self.app.root.visible = False
        self.app.root.hide()


    def _popup(self, widget, button, time, data=None):
        menu = Gtk.Menu()

        toggle = Gtk.MenuItem("Show / Hide")
        toggle.connect("activate", self.toggle_visibility)
        menu.append(toggle)

        menuitem_quit = Gtk.MenuItem("Quit")
        menuitem_quit.connect("activate", lambda *a: self.app.quit())
        menu.append(menuitem_quit)

        menu.show_all()
        menu.popup(None, None, None, self, 3, time)


    def do_deactivate(self):
        self.staticon.set_visible(False)
        del self.staticon


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

if __name__ == '__main__':
    argv = argparser()
    app = App() #argv)
    app.run(None)
    # exit_status = app.run(sys.argv)
    # print(exit_status)
    # sys.exit(exit_status)
