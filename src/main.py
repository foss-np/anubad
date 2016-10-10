#!/usr/bin/python3
#^^^ not using env for process name

__version__  = 0.97
__PKG_ID__   = "apps.anubad"
__PKG_NAME__ = "anubad - अनुवाद"
__PKG_DESC__ = "Translation Glossary and More"

import os, sys

__filepath__ = os.path.realpath(__file__)
PWD = os.path.dirname(__filepath__) + '/'

sys.path.append(PWD) # path-hack

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
    def __init__(self, app, visible=False):
        Gtk.StatusIcon.__init__(self)
        self.app = app

        self.makeWidgets()
        self.menuitem_visibility.set_active(visible)

        self.connect("activate", self.toggle_visibility)
        self.connect("popup_menu", self.on_secondary_click)
        self.connect("button-press-event", self.on_double_click)


    def makeWidgets(self):
        self.set_from_pixbuf(self.app.pixbuf_logo)
        self.set_title(__PKG_NAME__)
        # self.set_name(__PKG_ID__ + ".tray")
        ## BUG: don't use it ^^^ will create Gdk-CRITICAL
        self.set_tooltip_text(__PKG_DESC__)
        self.set_has_tooltip(True)

        self.menu = Gtk.Menu()

        self.menuitem_visibility = Gtk.CheckMenuItem("Show / Hide")
        self.menuitem_visibility.connect("toggled", self.toggle_visibility)
        self.menu.append(self.menuitem_visibility)

        menuitem_quit = Gtk.MenuItem("Quit")
        menuitem_quit.connect("activate", lambda *a: self.app.quit())
        self.menu.append(menuitem_quit)
        self.menu.show_all()


    def toggle_visibility(self, widget):
        if self.menuitem_visibility.get_active():
            self.app.activate()
            return

        self.app.home.hide()


    def on_secondary_click(self, widget, button, time):
        self.menu.popup(None, None, None, self, 3, time)


    def on_double_click(self, widget, event):
        if event.type != Gdk.EventType._2BUTTON_PRESS: return
        self.menuitem_visibility.set_active(
            not self.menuitem_visibility.get_active()
        )


class App(Gtk.Application):
    def __init__(self, opts):
        Gtk.Application.__init__(
            self,
            application_id = __PKG_ID__,
            flags = Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
        )

        self.opts = opts
        self.home = None
        self.connect("shutdown", self.on_shutdown)
        ## BUG: dont use =do_shutdown= virtual func, creates show
        ## CRITIAL error messages


    def do_startup(self):
        Gtk.Application.do_startup(self)
        self.commander = commander.Engine(self)
        self.commander.rc['version'] = lambda *a: str(__version__)
        self.commander.rc['help'] = lambda *a: self.on_help()

        self.cnf = setting.main(PWD)
        self.cnf.apply_args_request(self.opts)

        verify_mime(self.cnf)
        self.no_of_gloss = core.load_from_config(self.cnf)

        self.plugins = { k: v for k, v in scan_plugins(self.cnf) }

        self.icon_theme = Gtk.IconTheme.get_default()

        logo = self.icon_theme.load_icon(
            'accessories-dictionary', 128,
            Gtk.IconLookupFlags.FORCE_SVG
        )
        # NOTE: new 'accessories-dictionary' logo sucks, wtf aspect ratio
        self.pixbuf_logo = logo.scale_simple(128, 100, GdkPixbuf.InterpType.BILINEAR)


    def do_activate(self):
        if self.home == None:
            self.home = create_home_window(self.cnf, self.pixbuf_logo)
            self.add_window(self.home)
            self.home.engines.append((lambda q: q[0] == '>', self.commander.gui_adaptor))
            if self.cnf.preferences['show-on-system-tray']:
                self.tray = TrayIcon(self)
            self.no_of_plugins = load_plugins(self)
            welcome_message(self)
            if self.cnf.preferences['hide-on-startup']: return

        self.home.show()
        self.home.parse_geometry(self.cnf.gui['geometry'])
        self.home.present()


    def on_shutdown(self, app_obj):
        if self.home and self.cnf.preferences['enable-history-file']:
            print("shutdown: update history")
            # NOTE path expanded as the precaution if changed
            with open(os.path.expanduser(setting.FILE_HIST), mode='w+') as fp:
                fp.write('\n'.join(self.home.searchbar.entry.HISTORY))


    def do_command_line(self, command_line):
        opts = command_line.get_options_dict()
        argv = command_line.get_arguments()

        if len(argv) == 0:
            self.activate()
            return 0

        self.commander.execute(argv)

        if opts.contains("test"):
            print("Test argument recieved")

        return 0


def create_home_window(cnf, pixbuf_logo):
    home = ui.home.Home(core, cnf)
    home.set_icon(pixbuf_logo)
    home.set_title(__PKG_NAME__)
    home.set_wmclass("anubad.home", "anubad")
    home.connect('delete-event', confirm_exit)

    if cnf.preferences['show-on-taskbar']: home.set_skip_taskbar_hint(True)

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
        # BUG: app.quit() coz not quitting when emitted
        widget.destroy()
        return False

    return True


def create_about_dialog(pixbuf, parent=None):
    about = Gtk.AboutDialog(title="about", parent=parent)
    about.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
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
    logo = app.pixbuf_logo.scale_simple(36, 32, GdkPixbuf.InterpType.BILINEAR)
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
    b_help.connect('clicked', lambda w: on_help(app.home))
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
        # if not importlib.util.find_spec(key): # may be only for python3.5
        #     sys.path.append(plug['path'])
        if plug['path'] not in sys.path: sys.path.append(plug['path'])
        try:
            module = importlib.import_module(key)
        except:
            traceback.print_exception(*sys.exc_info())
            cnf.plugin_list[key]['error'] = True
            continue

        if not hasattr(module, 'plugin_main'):
            del module
            continue

        yield key, module


def load_plugins(app):
    if not app.cnf.preferences['enable-plugins']: return
    count = 0
    for key, module in app.plugins.items():
        plug = app.cnf.plugin_list[key]
        if plug['disable']:
            print("plugin.skipped.config.disabled:", key)
            continue

        platform = getattr(plug, '__platform__', os.name)
        if platform != os.name:
            plug['error'] = "incompatible platform"
            plug['platform']  = platform
            print("plugin.skipped.unmatch.platform:", key, platform)


        version = getattr(plug, '__version__', 0)
        if version > plug['version']:
            plug['error'] = "new version already exists"
            plug['version'] = version
            print("plugin.skipped.old.version:", key, version)

        require = getattr(plug, '__require__', __version__)
        if require > __version__:
            plug['error'] = "new version already exists"
            plug['require'] = version
            print("plugin.skipped.requires.anubad:", key, require)

        plug['depends']   = getattr(module, '__depends__', '')
        plug['authors']   = getattr(module, '__authors__', '')
        plug['support']   = getattr(module, '__support__', '')

        module.fp3 = fp3

        try:
            if module.plugin_main(app, PWD): continue
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


def parse_args():
    ap = argparse.ArgumentParser(
        prog='anubad',
        description=__PKG_DESC__
    )

    ap.add_argument(
        "--version",
        action  = "version",
        version = '%(prog)s v' + str(__version__))

    ap.add_argument(
        "--noplugins",
        action  = "store_true",
        default = False,
        help    = "Disable plugins loading")

    ap.add_argument(
        "--hide",
        action  = "store_true",
        default = False,
        help    = "Hide on startup")

    ap.add_argument(
        "--notray",
        action  = "store_true",
        default = False,
        help    = "Hide from notification tray")

    ap.add_argument(
        "--nohistfile",
        action  = "store_true",
        default = False,
        help    = "Disable history file")

    ap.add_argument(
        "--notaskbar",
        action  = "store_true",
        default = False,
        help    = "Hide from taskbar")

    ap.add_argument(
        "--nothread",
        action  = "store_true",
        default = False,
        help    = "Don't thread application")

    return ap


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    ap = parse_args()
    opts, commands = ap.parse_known_args()
    return App(opts), commands


if __name__ == '__main__':
    app, commands = main()
    app.run(commands)
