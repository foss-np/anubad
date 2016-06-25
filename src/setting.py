#!/usr/bin/env python3
"""Application Settings handler"""

import os
import configparser

FILE_CONF_DEFAULTS = '../config'
FILE_CONF = '~/.config/anubad/config'
FILE_HIST = '~/.cache/anubad/history'

SIZE_HIST  = 1024
SIZE_CACHE = 20


class Settings(configparser.ConfigParser):
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


    def __init__(self):
        # NOTE: object, aren't properly created for some unknown cause
        # until init was declared.
        pass

    def singleton_init(self):
        configparser.ConfigParser.__init__(self)
        self.glossary_list = []
        self.plugin_list   = dict()
        self.apps,        self['apps']        = None, dict()
        self.core,        self['core']        = None, dict()
        self.fonts,       self['fonts']       = None, dict()
        self.gui,         self['gui']         = None, dict()
        self.preferences, self['preferences'] = None, dict()


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
                obj  = self.extract_gloss(name, self[section])
                self.glossary_list.append(obj)

        self.gui   = self.extract_gui()
        self.apps  = self.extract_apps()
        self.fonts = self.extract_fonts()


    def extract_core(self):
        core = self['core']
        return {
            'debugly'        : core.get('debugly', ''),
            'plugins-folder' : core.get('plugins-folder', ''),
            'no-thread'      : core.getboolean('no-thread', False),
            'gloss-fix'      : core.getboolean('gloss-fix', False),
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


    def extract_gloss(self, name, obj):
        return {
            'name'        : name,
            'path'        : obj.get('path', ''),
            'pairs'       : obj.get('pairs', '').split(),
            'description' : obj.get('description', ''),
            'priority'    : obj.get('priority', '9'),
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


    def apply_args_request(self, opts):
        self.core['no-thread']                   = opts.nothread
        self.preferences['enable-plugins']      *= not opts.noplugins
        self.preferences['hide-on-startup']      = opts.hide
        self.preferences['show-on-system-tray'] *= not opts.notray
        self.preferences['enable-history-file'] *= not opts.nohistfile
        if self.preferences['show-on-system-tray']:
            self.preferences['show-on-taskbar'] *= opts.notaskbar


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
    cnf = Settings()
    cnf.read(PWD + FILE_CONF_DEFAULTS)
    cnf.read(FILE_CONF)
    cnf.load()
    return cnf


if __name__ == '__main__':
    cnf = main()
    from pprint import pprint

    pprint(cnf.apps)
    pprint(cnf.core)
    pprint(cnf.fonts)
    pprint(cnf.gui)
    pprint(cnf.preferences)

    pprint(cnf.glossary_list)
