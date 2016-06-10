#!/usr/bin/env python3

"""
not really required plugins, tricks for developers.
"""

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

import os
import linecache
from subprocess import Popen
from subprocess import check_output

import config

def open_dir(root):
    root.toolbar.t_COPY.set_active(False)
    path  = root.rc.glossary_list['foss']['pairs'][0]
    explorer = root.rc.apps['file-manager']
    print("pid:", Popen([explorer, path]).pid)


def file_browser(app):
    b_OPEN = Gtk.ToolButton(icon_name=Gtk.STOCK_OPEN)
    app.insert_plugin_item_on_toolbar(b_OPEN)
    b_OPEN.set_tooltip_markup("Open Glossary Directory")
    b_OPEN.connect("clicked", lambda *a: open_dir(app.root))
    b_OPEN.show()


def shell_engine(root, query):
    # TODO handle error, exit != 0
    output = check_output(query.split(), universal_newlines=True)
    begin = root.viewer.textbuffer.get_start_iter()
    root.viewer.textbuffer.place_cursor(begin)
    root.viewer.insert_at_cursor("\n")
    if output == '':
        root.viewer.not_found(query, "nothing in stdout")
        return

    root.search_entry.set_text("$ ")
    root.search_entry.set_position(2)
    root.viewer.insert_at_cursor(output)


def dump_engine(root, query):
    FULL, FUZZ = root.core.Glossary.search(query)
    output = ""
    for word, ID, src in FULL:
        ## handel invert map
        ## TODO: change the style
        if type(ID) == int: output += linecache.getline(src, ID)
        else:
            for element in ID:
                output += linecache.getline(src, element)

    begin = root.viewer.textbuffer.get_start_iter()
    root.viewer.textbuffer.place_cursor(begin)
    root.viewer.insert_at_cursor("\n")
    if output == '':
        root.viewer.not_found(query)
        return

    root.viewer.insert_at_cursor(output)


def file_opener(root, cmd):
    if len(cmd) < 2:
        output  = "Accessable files\n\t$"
        output += '\n\t$'.join(attr for attr in dir(config) if attr.startswith("FILE"))
        return output

    if cmd[1].startswith('$'):
        arg1 = cmd[1].strip('$')
        if hasattr(config, arg1):
            var = getattr(config, arg1)
        else:
            return "'%s' undefined variable"%cmd[1]
    else: var = ''.join(cmd[1:])

    path = os.path.expanduser(var)
    if os.path.isfile(path):
        return str(Popen(root.rc.editor_goto_line_uri(path)))

    return "'%s' file not found"%path

commands = {
    'history'      : (lambda root, *a: '\n'.join(root.search_entry.HISTORY)),
    'file'         : file_opener,
    'count'        : (lambda root, *a: "not implemented"),
    'stats'        : (lambda root, *a: "not implemented"),
    'list'         : (lambda root, *a: "not implemented"),
}


def command_engine(root, query):
    cmd = query.split()
    for key, func in commands.items():
        if key == cmd[0]:
            output = func(root, cmd)
            break
        output = "Invalid command"


    begin = root.viewer.textbuffer.get_start_iter()
    root.viewer.textbuffer.place_cursor(begin)
    root.viewer.insert_at_cursor("\n")
    root.viewer.insert_at_cursor(output)
    root.search_entry.set_text("> ")
    root.search_entry.set_position(2)

    print(root.search_entry.get_icon_name(0))
    print(root.search_entry.get_icon_stock(0))
    print(root.search_entry.get_icon_tooltip_text(0))
    print(root.search_entry.get_icon_tooltip_markup(0))



def python_engine(root, query):
    # try:
    #     if not hasattr(root, query):
    #         output = "doesn't have anything like that"
    # except
    output = "python engine not implemented"
    begin = root.viewer.textbuffer.get_start_iter()
    root.viewer.textbuffer.place_cursor(begin)
    root.viewer.insert_at_cursor("\n")
    root.viewer.insert_at_cursor(output)
    root.search_entry.set_text(">>> ")
    root.search_entry.set_position(4)


def plugin_main(app, fullpath):
    file_browser(app)
    app.root.engines.append((lambda q: q[0] == '$', lambda q: shell_engine(app.root, q[1:].strip())))
    app.root.engines.append((lambda q: q.startswith('>>>'), lambda q: python_engine(app.root, q[3:].strip())))
    app.root.engines.append((lambda q: q[0] == '>', lambda q: command_engine(app.root, q[1:].strip())))
    app.root.engines.append((lambda q: q.startswith('d:'), lambda q: dump_engine(app.root, q[2:].strip())))
    return True
