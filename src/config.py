#!/usr/bin/env python3
"""
config file parser with with robust error handeling
"""

import os
import configparser

FILE_CONF_DEFAULTS = '../config'
FILE_CONF = '~/.config/anubad/config'
FILE_HIST = '~/.cache/anubad/history'

SIZE_HIST  = 1024
SIZE_CACHE = 20


class RC(configparser.ConfigParser):
    MIME_TYPES = (
        ("file-manager", "inode/directory"),
        ("editor", "text/plain"),
        ("browser", "x-scheme-handler/https"),
    )

    __instance__ = None

    def __new__(cls, *args, **kargs):
        """Override the __new__ method to make singleton"""
        if cls.__instance__ is None:
            cls.__instance__ = configparser.ConfigParser.__new__(cls)
            cls.__instance__.singleton_init(*args, **kargs)
        return cls.__instance__


    def singleton_init(self):
        configparser.ConfigParser.__init__(self)
        self.glossary_list = dict()
        self.apps,        self['apps']        = dict(), dict()
        self.core,        self['core']        = dict(), dict()
        self.fonts,       self['fonts']       = dict(), dict()
        self.gui,         self['gui']         = dict(), dict()
        self.preferences, self['preferences'] = dict(), dict()


    def read(self, conf_file):
        path = os.path.expanduser(conf_file)
        if not os.path.isfile(path): return
        configparser.ConfigParser.read(self, path)


    def load(self):
        self.core = self.extract_core()
        self.preferences = self.extract_preferences()

        for section in self.sections():
            if 'gloss' in section:
                name = section.split('"')[1]
                obj  = self.extract_gloss(self[section])
                self.glossary_list[name] = obj

        self.fonts = self.extract_fonts()
        self.gui = self.extract_gui()
        self.apps = self.extract_apps()


    def extract_core(self):
        core = self['core']
        return {
            'debugly'   : core.get('debugly', ''),
            'plugins'   : core.get('plugins', ''),
            'gloss-fix' : core.getboolean('gloss-fix', False),
        }


    def extract_preferences(self):
        pref = self['preferences']

        return {
            'enable-history-file' : pref.getboolean('enable-entry-history', True),
            'show-on-system-tray' : pref.getboolean('show-on-system-tray', True),
            'use-system-defaults' : pref.getboolean('use-system-defaults', True),
            'remember-gui-state'  : pref.getboolean('remember-gui-state', False),
            'show-on-taskbar'     : pref.getboolean('show-on-taskbar', True),
            'hide-on-startup'     : pref.getboolean('hide-on-startup', True),
            'enable-plugins'      : pref.getboolean('enable-plugins', True),
            'append-at-end'       : pref.getboolean('append-at-end', False),
            'regex-search'        : pref.getboolean('regex-search', True),
        }


    def extract_gloss(self, obj):
        path = obj.get('path')
        return {
            'pairs'       : [ path + p + '/' for p in obj.get('pairs').split() ],
            'description' : obj.get('description', ''),
            'priority'    : obj.getboolean('priority', 5),
            'read-only'   : obj.getboolean('read-only', True),
            'fetch'       : obj.get('fetch', True),
        }


    def extract_fonts(self):
        font = self['fonts']
        return {
            'viewer' : font.get('viewer', 'DejaVu Sans Mono 13'),
        }


    def extract_gui(self):
        ui = self['gui']
        return {
            'state'    : ui.get('wm-state', 'normal'),
            'geometry' : ui.get('geometry', '600x550'),
        }


    def extract_apps(self):
        apps = self['apps']
        return {
            'file-manager' : apps.get('file-manager'),
            'editor'       : apps.get('editor'),
            'browser'      : apps.get('browser'),
        }


    def editor_goto_line_uri(self, path, line=None):
        ed = self.apps['editor']
        if line is None: return [ ed, path ]

        if   ed == "leafpad" : cmd = [ ed, "--jump=%d"%line, path ]
        elif ed == "gedit"   : cmd = [ ed, "+%d "%line, path ]
        elif ed == "emacs"   : cmd = [ ed, "+%d "%line, path ]
        elif "subl" in ed    : cmd = [ ed + ":%d "%line, path ]
        else: cmd = [ ed, path ]
        return cmd


def main(PWD=""):
    rc = RC()
    rc.read(PWD + FILE_CONF_DEFAULTS)
    rc.read(FILE_CONF)
    rc.load()
    return rc


if __name__ == '__main__':
    rc = main()
    from pprint import pprint

    pprint(rc.apps)
    pprint(rc.core)
    pprint(rc.fonts)
    pprint(rc.gui)
    pprint(rc.preferences)

    pprint(rc.glossary_list)
