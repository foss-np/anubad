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
        self.commander.rc['version'] = lambda *a: str(__version__)
        self.commander.rc['help'] = lambda *a: self.on_help()

        self.cnf = setting.main(PWD)
        self.cnf.apply_args_request(self.opts)

        verify_mime(self.cnf)
        self.no_of_gloss = core.load_from_config(self.cnf)

        self.plugins = { k: v for k, v in scan_plugins(self.cnf) }
        # NOTE: since new 'accessories-dictionary' logo sucks, wtf aspect ratio
        self.pixbuf_logo = GdkPixbuf.Pixbuf.new_from_file(PWD + '../assets/anubad.png')


    def do_activate(self):
        if self.home == None:
            self.home = create_home_window(self.cnf, self.pixbuf_logo)
            self.add_window(self.home)
            self.home.engines.append((lambda q: q[0] == '>', self.commander.gui_adaptor))
            if self.cnf.preferences['show-on-system-tray']:
                self.tray = TrayIcon(self, self.cnf.preferences['hide-on-startup'])
            self.no_of_plugins = load_plugins(self)
            welcome_message(self)
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


def create_home_window(cnf, pixbuf_logo):
    home = ui.home.Home(core, cnf)
    home.set_icon(pixbuf_logo)
    home.set_title(__PKG_NAME__)
    home.connect('delete-event', confirm_exit)

    if cnf.preferences['show-on-taskbar']    : home.set_skip_taskbar_hint(True)

    histfile = os.path.expanduser(setting.FILE_HIST)
    if cnf.preferences['enable-history-file'] and os.path.exists(histfile):
        home.searchbar.entry.HISTORY += open(
            histfile, encoding = "UTF-8"
        ).read().splitlines()
        home.searchbar.entry.CURRENT = len(home.searchbar.entry.HISTORY)

    home.toolbar.b_HELP = Gtk.ToolButton(icon_name="help-contents")
    home.toolbar.add(home.toolbar.b_HELP)
    home.toolbar.b_HELP.show()
    home.toolbar.b_HELP.set_tooltip_markup("Help")
    home.toolbar.b_HELP.connect('clicked', lambda w: on_help(home))

    home.toolbar.b_ABOUT = Gtk.ToolButton(icon_name="help-about")
    home.toolbar.add(home.toolbar.b_ABOUT)
    home.toolbar.b_ABOUT.show()
    home.toolbar.b_ABOUT.set_tooltip_markup("About")
    home.toolbar.b_ABOUT.connect("clicked", lambda w: create_about_dialog(pixbuf_logo, home))
    return home


def confirm_exit(widget, event):
    dialog = Gtk.MessageDialog(
        transient_for=widget,
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
        # FIXME app.quit() coz not quitting when emitted
        app.quit()
        return False

    return True


def create_about_dialog(pixbuf, parent=None):
    about = Gtk.AboutDialog(title="about", parent=parent)
    about.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
    # about.set_logo_icon_name('accessories-dictionary')
    about.set_logo(pixbuf)
    about.set_program_name(__PKG_NAME__)
    about.set_comments("%s\n\nv%s\n"%(__PKG_DESC__, __version__))
    about.set_website("http://anubad.herokuapp.com")
    about.set_website_label("Web Version")
    about.set_authors(open(PWD + '../AUTHORS').read().splitlines())
    about.set_license(open(PWD + '../LICENSE').read())
    about.run()
    about.destroy()


def on_help(home):
    screen = home.get_screen();
    Gtk.show_uri(screen, "help:anubad", Gtk.get_current_event_time());


def welcome_message(app):
    viewer = app.home.viewer

    end = viewer.textbuffer.get_end_iter()
    logo = app.pixbuf_logo.scale_simple(32, 32, GdkPixbuf.InterpType.BILINEAR)
    viewer.textbuffer.insert_pixbuf(end, logo)
    viewer.insert_at_cursor("\nanubad", viewer.tag_bold)
    viewer.insert_at_cursor(" v%s"%__version__, viewer.tag_hashtag)
    viewer.insert_at_cursor("\n%s\n\n"%__PKG_DESC__, viewer.tag_source)

    viewer.insert_at_cursor("%2d glossary loaded\n"%app.no_of_gloss)
    viewer.insert_at_cursor("%2d plugins loaded\n"%app.no_of_plugins)
    viewer.insert_at_cursor("For help click ")

    end    = viewer.textbuffer.get_end_iter()
    anchor = viewer.textbuffer.create_child_anchor(end)
    b_help = Gtk.ToolButton(icon_name='help-contents')
    b_help.connect('clicked', lambda w: app.on_help())
    b_help.show()
    viewer.textview.add_child_at_anchor(b_help, anchor)
    viewer.insert_at_cursor(" or press")
    viewer.insert_at_cursor(" F1", viewer.tag_bold)


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

    for file_name in os.listdir(path_plugins):
        if '#' in file_name: continue # just for ignoring backup files
        if file_name[-3:] not in ".py": continue
        _id = file_name[:-3]
        new_plug = cnf.plugin_list.get(
            _id,
            cnf.new_plugin(_id)
        )

        new_plug['path'] = path_plugins
        cnf.plugin_list[_id] = new_plug


    for key, plug in cnf.plugin_list.items():
        if plug['path'] not in sys.path: sys.path.append(plug['path'])

        try:
            namespace = importlib.__import__(key)
        except:
            traceback.print_exception(*sys.exc_info())
            cnf.plugin_list[key]['error'] = True
            continue

        if not hasattr(namespace, 'plugin_main'):
            del namespace
            continue

        yield key, namespace


def load_plugins(app):
    if not app.cnf.preferences['enable-plugins']: return
    count = 0
    for key, namespace in app.plugins.items():
        plug = app.cnf.plugin_list[key]
        if plug['disable']:
            print("plugin.skipped.config.disabled:", key)
            continue

        if getattr(plug, '__platform__', os.name) != os.name:
            print("plugin.skipped.unmatch.platform:", key)
            continue

        try:
            if namespace.plugin_main(app, PWD): continue
        except Exception as e:
            plug['error'] = True
            traceback.print_exception(*sys.exc_info())
            app.home.infobar.set_message_type(Gtk.MessageType.WARNING)
            app.home.infobar.LABEL.set_markup("Error occured during loading plugin <b>%s</b>"%key)
            app.home.infobar.show_all()
            continue

        plug['active'] = True
        print("plugin.loaded:", key, file=sys.stderr)
        count += 1
    return count


def create_arg_parser():
    parser = argparse.ArgumentParser(
        prog='anubad',
        description=__PKG_DESC__
    )

    parser.add_argument(
        "--version",
        action  = "version",
        version = '%(prog)s v' + str(__version__))

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
