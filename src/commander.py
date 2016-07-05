#!/usr/bin/env python3

import os, sys

from gi.repository import Gio

from pprint import pformat
from subprocess import Popen
import setting
import core

class Engine:
    def __init__(self, app=None):
        self.app = app
        self.rc = {
            'exit'     : lambda *a: app.quit(),
            'file'     : self.file_type,
            'hashtags' : self.hashtags,
            'history'  : self.history,
            'open'     : self.file_opener,
            'quit'     : lambda *a: app.quit(),
            'search'   : self.search,
            'set'      : self.set,
            'stats'    : self.stats,
        }


    def execute(self, args):
        for key, func in self.rc.items():
            if key == args[0]:
                return func(args)


    def gui_adaptor(self, query):
        args = query[1:].strip().split()
        if len(args) == 0: return

        output = self.execute(args)
        if output is None:
            output  = "'%s' is not a valid command,\n"%args[0]
            output += "avaliable commands\n\t"
            output += '\n\t'.join(self.rc)

        self.app.home.searchbar.entry.set_text("> ")
        self.app.home.searchbar.entry.set_position(2)

        return output

    def search(self, args):
        query = ' '.join(args[1:])
        if self.app.home:
            self.app.home.searchbar.entry.set_text(query)
            self.app.home.search_and_reflect(query)
        else:
            print(query)
            # TODO show only exact match
            print(core.Glossary.search(query))


    def history(self, args):
        return '\n'.join(self.app.home.searchbar.entry.HISTORY)


    def set(self, args):
        return pformat(self.app.cnf.core)


    def hashtags(self, args):
        output = ""
        for tag, count in self.app.home.core.Glossary.hashtags.items():
            output += "%-40s (%d)\n"%(tag, count)
        return output


    def file_type(self, args):
        if len(args) < 2:
            return "Argument Missing\n"

        path = os.path.expanduser(' '.join(args[1:]))
        output = Gio.content_type_guess(path)
        print(output)
        return output[0]


    def file_opener(self, args):
        if len(args) < 2:
            output  = "Argument Missing\n"
            output += "Accessable files\n\t$"
            output += '\n\t$'.join(attr for attr in dir(setting) if attr.startswith("FILE"))
            return output

        if args[1].startswith('$'):
            arg1 = args[1].strip('$')
            if hasattr(setting, arg1):
                var = getattr(setting, arg1)
            else:
                return "'%s' undefined variable"%args[1]
        else: var = ' '.join(args[1:])

        path = os.path.expanduser(var)
        if os.path.isdir(path):
            return str(Popen([self.app.cnf.apps['file-manager'], path]))

        if not os.path.isfile(path):
            return "'%s' is invalid"%path

        _type = self.file_type(['file', path])
        executable = None
        for key, val in self.app.cnf.MIME_TYPES:
            if val == _type:
                executable = self.app.cnf.apps[key]
                break
        else:
            desktopAppInfo = Gio.app_info_get_default_for_type(_type, 0)
            executable = desktopAppInfo.get_executable()

        print(executable, path)
        return str(Popen([executable, path]))


    def stats(self, *a):
        output = ""
        for path, instance in self.app.home.core.Glossary.instances.items():
            output += "%s : %d \n"%(path, instance.counter)
        return output


def sample():
    engine = Engine()


if __name__ == '__main__':
    sample()
