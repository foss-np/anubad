#!/usr/bin/env python3
"""
config file handeler with with robust error handeling
"""

import os
import configparser

FILE_CONF_DEFAULTS = '../config'
FILE_CONF = os.path.expanduser('~/.config/anubad/config')

from pprint import pprint

class RC(configparser.ConfigParser):
    type_list = (
        ("file-manager", "inode/directory"),
        ("editor", "text/plain"),
        ("browser", "x-scheme-handler/https")
    )

    def __init__(self):
        configparser.ConfigParser.__init__(self)

        self.glossary_list = []
        self.plugin = {}
        self.preferences = {}
        self.fonts = {}
        self.ui = {}
        self.apps = {}


    def load(self):
        for section in self.sections():
            if 'gloss' in section:
                self.list_gloss(self[section])

        self.list_preference()
        self.list_font()
        self.list_gui_states()
        self.list_default_app()

        self.plugin = self['plugins'] if 'plugins' in self.sections() else {
            'path': ''
        }


    def list_gloss(self, obj):
        path = obj.get('path')
        self.glossary_list.append({
            'pairs'       : [ path + p + '/' for p in obj.get('pairs').split() ],
            'description' : obj.get('description', ''),
            'priority'    : obj.getboolean('priority', 5),
            'read-only'   : obj.getboolean('read-only', True),
            'fetch'       : obj.get('fetch', True)
        })


    def list_font(self):
        font = self['fonts'] if 'fonts' in self.sections() else {}
        self.fonts = {
            'viewer' : font.get('viewer', 'DejaVu Sans Mono 13')
        }


    def list_gui_states(self):
        ui = self['gui'] if 'gui' in self.sections() else {}
        self.ui = {
            'state'    : ui.get('wm-state', 'normal'),
            'geometry' : ui.get('geometry', '600x550')
        }


    def list_preference(self):
        pref = self['preferences'] if 'preferences' in self.sections() else {}
        self.preferences = {
            'use-system-defaults' : pref.getboolean('use-system-defaults', True),
            'append-at-end'       : pref.getboolean('append-at-end', False),
            'regex-search'        : pref.getboolean('regex-search', True),
            'word-net'            : pref.getboolean('word-net', False)
        }


    def list_default_app(self):
        apps = self['apps'] if 'apps' in self.sections() else {}

        self.apps = {
            'file-manager' : apps.get('file-manager'),
            'editor'       : apps.get('editor'),
            'browser'      : apps.get('browser')
        }


    def editor_goto_line_uri(self, path, line):
        ed = self.apps['editor']
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
    pprint(rc.fonts)
    pprint(rc.glossary_list)
