#!/usr/bin/python3
#^^^ not using env for process name

__version__  = 0.97
__PKG_ID__   = "apps.anubad"
__PKG_NAME__ = "anubad - अनुवाद"
__PKG_DESC__ = "Translation Glossary and More"

import os, sys

__filepath__ = os.path.realpath(__file__)
PWD = os.path.dirname(__filepath__) + '/'

sys.path.append(PWD)

import argparse
import signal
import traceback
import importlib

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk
from gi.repository import GLib, Gio
from gi.repository import GdkPixbuf

import setting
import core
import commander

import ui.home
fp_DEVNULL = open(os.devnull, 'w')
VERBOSE = int(os.environ.get("VERBOSE", 0))
for i in range(3, 7):
    if VERBOSE > 0:
        print(
            "VERBOSE: %d fp%d enabled"%(VERBOSE, i),
            file=sys.stderr
        )
        stream = "sys.stderr"
        VERBOSE -= 1
    else:
        stream = "fp_DEVNULL"
    exec("fp%d = %s"%(i, stream))

core.fp3 = ui.home.fp3 = fp3
core.fp4 = ui.home.fp4 = fp4


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
        self.commander = commander.Engine(app)

        self.cnf = setting.main(PWD)
        self.cnf.apply_args_request(self.opts)

        verify_mime(self.cnf)
        self.no_of_gloss = core.load_from_config(self.cnf)

        self.plugins = { k: v for k, v in scan_plugins(self.cnf) }
        # NOTE: since 'accessories-dictionary' logo sucks
        self.pixbuf_logo = GdkPixbuf.Pixbuf.new_from_file(PWD + '../assets/anubad.png')


    def do_activate(self):
        if self.home == None:
            self.home = self.home_create_window()
            self.no_of_plugins = load_plugins(self)
            if self.cnf.preferences['hide-on-startup']: return

        self.home.show()
        self.home.parse_geometry(self.cnf.gui['geometry'])
        self.home.present()


    def do_shutdown(self):
        if self.home and self.cnf.preferences['enable-history-file']:
            print("shutdown: update history")
            # NOTE path expanded as the precaution if changed
            fp = open(os.path.expanduser(setting.FILE_HIST), mode='w+')
            fp.write('\n'.join(self.home.searchbar.entry.HISTORY))
            fp.close()
        self.quit()


    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        argv = command_line.get_arguments()

        if len(argv) == 0:
            self.activate()
            return 0

        self.commander.execute(argv)

        if options.contains("test"):
            print("Test argument recieved")

        return 0


    def home_create_window(self):
        home = ui.home.Home(core, self.cnf)
        self.add_window(home)
        home.set_icon(self.pixbuf_logo)
        home.set_title(__PKG_NAME__)
        home.connect('delete-event', self.home_on_destroy)

        self.add_buttons_on_toolbar(home.toolbar)
        home.engines.append((lambda q: q[0] == '>', self.commander.gui_adaptor))

        if self.cnf.preferences['show-on-taskbar']    : home.set_skip_taskbar_hint(True)
        if self.cnf.preferences['show-on-system-tray']:
            self.tray = TrayIcon(self, self.cnf.preferences['hide-on-startup'])

        histfile = os.path.expanduser(setting.FILE_HIST)
        if self.cnf.preferences['enable-history-file'] and os.path.exists(histfile):
            home.searchbar.entry.HISTORY += open(
                histfile, encoding = "UTF-8"
            ).read().splitlines()
            home.searchbar.entry.CURRENT = len(home.searchbar.entry.HISTORY)

        return home


    def home_on_destroy(self, event, *args):
        dialog = Gtk.MessageDialog(
            transient_for=self.home,
            modal=True,
            buttons=Gtk.ButtonsType.OK_CANCEL
        )

        dialog.props.text = 'Are you sure you want to quit?'
        def on_key_release(widget, event):
            if Gdk.ModifierType.CONTROL_MASK & event.state:
                if event.keyval in (ord('q'), ord('Q'),  ord('c'), ord('C')):
                    dialog.emit('response', Gtk.ResponseType.OK)

        dialog.connect('key_release_event', on_key_release)

        response = dialog.run()
        dialog.destroy()

        if response == Gtk.ResponseType.OK:
            self.quit()
            return False

        return True


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


    def add_buttons_on_toolbar(self, bar):
        bar.b_ABOUT = Gtk.ToolButton(icon_name="help-about")
        bar.add(bar.b_ABOUT)
        bar.b_ABOUT.show()
        bar.b_ABOUT.set_tooltip_markup("About")

        def about_dialog(widget):
            about = Gtk.AboutDialog(title="anubad", parent=self.home)
            about.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
            about.set_logo(self.pixbuf_logo)
            about.set_program_name(__PKG_NAME__)
            about.set_comments("%s\n\nv%s\n"%(__PKG_DESC__, __version__))
            about.set_website("http://anubad.herokuapp.com")
            about.set_website_label("Web Version")
            about.set_authors(open(PWD + '../AUTHORS').read().splitlines())
            about.set_license(open(PWD + '../LICENSE').read())
            about.run()
            about.destroy()

        bar.b_ABOUT.connect("clicked", about_dialog)


def verify_mime(cnf):
    for name, _type in cnf.MIME_TYPES:
        if not cnf.preferences['use-system-defaults']:
            if cnf.apps[name]: continue
        desktopAppInfo = Gio.app_info_get_default_for_type(_type, 0)
        cnf.apps[name] = desktopAppInfo.get_executable()


def scan_plugins(cnf):
    if not cnf.preferences['enable-plugins']: return
    path_plugins = PWD + cnf.core['plugins-folder']
    if not os.path.isdir(path_plugins): return
    if path_plugins == PWD: return
    sys.path.append(path_plugins)

    for file_name in os.listdir(path_plugins):
        if '#' in file_name: continue # just for ignoring backup files
        if file_name[-3:] not in ".py": continue
        name = file_name[:-3]
        try:
            namespace = importlib.__import__(name)
        except:
            traceback.print_exception(*sys.exc_info())
            continue

        if not hasattr(namespace, 'plugin_main'):
            del namespace
            continue

        plug = cnf.plugin_list.get(
            name,
            {
                'registered' : False,
                'disable'    : False,
            }
        )

        plug['active']    = False
        plug['error']     = False
        plug['platform']  = getattr(namespace, '__platform__', os.name)
        plug['for']       = getattr(namespace, '__for__', __version__)
        plug['version']   = getattr(namespace, '__version__', 0)
        plug['depends']   = getattr(namespace, '__depends__', '')
        plug['authors']   = getattr(namespace, '__authors__', '')
        plug['support']   = getattr(namespace, '__support__', '')

        cnf.plugin_list[name] = plug
        yield name, namespace


def load_plugins(app):
    if not app.cnf.preferences['enable-plugins']: return
    count = 0
    for name, plug in app.cnf.plugin_list.items():
        if plug['disable']:
            print("plugin.skipped.config.disabled:", name)
            continue

        if plug['platform'] != os.name:
            print("plugin.skipped.unmatch.platform:", name)
            continue

        try:
            if app.plugins[name].plugin_main(app, PWD): continue
            plug['active'] = True
            print("plugin.loaded:", name, file=sys.stderr)
            count += 1
        except Exception as e:
            plug['error'] = True
            traceback.print_exception(*sys.exc_info())
            app.home.infobar.set_message_type(Gtk.MessageType.WARNING)
            app.home.infobar.LABEL.set_markup("Error occured during loading plugin <b>%s</b>"%name)
            app.home.infobar.show_all()

    return count


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
