#!/usr/bin/env python3
"""Application Settings handler"""

import os
import configparser

PATH_INI  = '~/.config/'
PATH_CACHE = '~/.cache/anubad/'

FILE_INI          = PATH_INI + 'anubad.ini'
FILE_HIST         = PATH_CACHE + 'history'
FILE_DEFAULT_INI  = '../default.ini'

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


    def __init__(self, pwd=""):
        # NOTE: object, aren't properly created for some unknown cause
        # until init was declared.
        pass


    def singleton_init(self, pwd=""):
        configparser.ConfigParser.__init__(self)
        self.PWD = pwd
        self.glossary_list = []
        self.plugin_list   = dict()
        self.gui,         self['gui']         = None, dict()
        self.apps,        self['apps']        = None, dict()
        self.core,        self['core']        = None, dict()
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
                _id = section.split('"')[1]
                obj = self.new_gloss(_id, self[section])
                self.glossary_list.append(obj)
                continue

            if 'plugin' in section:
                _id = section.split('"')[1]
                obj = self.new_plugin(_id, self[section])
                self.plugin_list[_id] = obj


        self.gui   = self.extract_gui()
        self.apps  = self.extract_apps()


    def new_gloss(self, _id, obj):
        return {
            'name'        : obj.get('name', _id),
            'path'        : obj.get('path', ''),
            'type'        : obj.get('type', 'local'),
            'pairs'       : obj.get('pairs', '').split(),
            'fetch'       : obj.get('fetch', None),
            'version'     : obj.getfloat('version', 0),
            'priority'    : obj.getint('priority', 9),
            'read-only'   : obj.getboolean('read-only', True),
            'description' : obj.get('description', ''),
            'active'      : False,
            'error'       : True,
        }


    def new_plugin(self, _id, obj=None):
        # NOTE: this is just the wrapper for central var control
        ## dict() should send var in its own datatype
        get        = obj.get        if hasattr(obj, 'get') else lambda k, d: d
        getint     = obj.getint     if hasattr(obj, 'getint') else lambda k, d: get(k, d)
        getfloat   = obj.getfloat   if hasattr(obj, 'getfloat') else lambda k, d: get(k, d)
        getboolean = obj.getboolean if hasattr(obj, 'getboolean') else lambda k, d: get(k, d)

        return {
            'name'       : get('name', _id),
            'path'       : get('path', ''),
            'fetch'      : get('fetch', None),
            'version'    : getfloat('version', 0),
            'disable'    : getboolean('disable', False),
            'priority'   : getint('priority', 9),
            'platform'   : get('platform', os.name),
            'registered' : True if obj else False,
            'active'     : False,
            'error'      : False,
        }


    def extract_core(self):
        core = self['core']
        return {
            'debugly'        : core.get('debugly', ''),
            'no-thread'      : core.getboolean('no-thread', True),
            'gloss-fix'      : core.getboolean('gloss-fix', False),
            'plugins-folder' : core.get('plugins-folder', ''),
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
            'browser'      : apps.get('browser'),
            'editor'       : apps.get('editor'),
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


def main(pwd=""):
    cnf = Settings(pwd)
    global FILE_DEFAULT_INI
    FILE_DEFAULT_INI = pwd + FILE_DEFAULT_INI
    cnf.read(FILE_DEFAULT_INI)
    cnf.read(FILE_INI)
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
