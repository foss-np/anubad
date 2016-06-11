#!/usr/bin/env python3

"""
not really required plugins, tricks for developers.
"""

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk

import os
import linecache
from subprocess import Popen
from subprocess import check_output

import config

def plugin_open_dir(app):
    b_OPEN = Gtk.ToolButton(icon_name=Gtk.STOCK_OPEN)
    app.insert_plugin_item_on_toolbar(b_OPEN)
    b_OPEN.set_tooltip_markup("Open Glossary Directory")

    def _browse(*arg):
        app.home.toolbar.t_COPY.set_active(False)
        path  = home.rc.glossary_list['foss']['pairs'][0]
        explorer = home.rc.apps['file-manager']
        print("pid:", Popen([explorer, path]).pid)

    b_OPEN.connect("clicked", _browse)
    b_OPEN.show()


def plugin_open_src(app):
    def _edit():
        app.home.toolbar.t_COPY.set_active(False)
        treeSelection = app.home.sidebar.treeview.get_selection()
        model, pathlst = treeSelection.get_selected_rows()

        if len(pathlst) == 0:
            path  = app.home.rc.glossary_list['foss']['pairs'][0]
            gloss = app.home.core.Glossary.instances[path]
            src   = path + 'main.tra'
            line  = gloss.counter
        else:
            word, ID, src, parsed_info  = app.home.sidebar.get_suggestion(pathlst[0])
            # print(row, file=fp6)

            ## handel invert map
            ## TODO: change the style
            if type(ID) == int: line = ID
            else: # else tuple
                try:
                    i = app.home.clips.index(app.home.copy_buffer)
                    # print(i, file=fp6)
                    # print(ID, i)
                    line = ID[i]
                except ValueError:
                    line = None

        cmd = app.home.rc.editor_goto_line_uri(src, line)
        print("pid:", src, Popen(cmd).pid)

    def _on_key_release(widget, event):
        if Gdk.ModifierType.MOD1_MASK & event.state:
            if event.keyval == ord('e'): _edit()

    app.home.connect('key_release_event', _on_key_release)


def engine_shell(home, query):
    # TODO handle error, exit != 0
    output = check_output(query.split(), universal_newlines=True)
    begin = home.viewer.textbuffer.get_start_iter()
    home.viewer.textbuffer.place_cursor(begin)
    home.viewer.insert_at_cursor("\n")
    if output == '':
        home.viewer.not_found(query, "nothing in stdout")
        return

    home.search_entry.set_text("$ ")
    home.search_entry.set_position(2)
    home.viewer.insert_at_cursor(output)


def engine_dump(home, query):
    FULL, FUZZ = home.core.Glossary.search(query)
    output = ""
    for word, ID, src in FULL:
        ## handel invert map
        ## TODO: change the style
        if type(ID) == int: output += linecache.getline(src, ID)
        else:
            for element in ID:
                output += linecache.getline(src, element)

    begin = home.viewer.textbuffer.get_start_iter()
    home.viewer.textbuffer.place_cursor(begin)
    home.viewer.insert_at_cursor("\n")
    if output == '':
        home.viewer.not_found(query)
        return

    home.viewer.insert_at_cursor(output)


def file_opener(app, args):
    if len(args) < 2:
        output  = "Accessable files\n\t$"
        output += '\n\t$'.join(attr for attr in dir(config) if attr.startswith("FILE"))
        return output

    if args[1].startswith('$'):
        arg1 = args[1].strip('$')
        if hasattr(config, arg1):
            var = getattr(config, arg1)
        else:
            return "'%s' undefined variable"%args[1]
    else: var = ''.join(args[1:])

    path = os.path.expanduser(var)
    if os.path.isfile(path):
        return str(Popen(app.home.rc.editor_goto_line_uri(path)))

    return "'%s' file not found"%path

def stats(app, *a):
    output = ""
    for path, instance in app.home.core.Glossary.instances.items():
        output += "%s : %d \n"%(path, instance.counter)
    return output


commands = {
    'history'      : (lambda app, *a: '\n'.join(app.home.search_entry.HISTORY)),
    'edit'         : file_opener,
    'count'        : (lambda app, *a: "not implemented"),
    'stats'        : stats,
    'gloss'        : (lambda app, *a: "not implemented"),
}

def engine_cmd(app, query):
    cmd = query.split()
    if len(cmd) == 0: return

    for key, func in commands.items():
        if key == cmd[0]:
            output = func(app, cmd)
            break
    else:
        output  = "'%s' is not a valid command,\n"%cmd[0]
        output += "avaliable commands\n\t"
        output += '\n\t'.join(commands)

    begin = app.home.viewer.textbuffer.get_start_iter()
    app.home.viewer.textbuffer.place_cursor(begin)
    app.home.viewer.insert_at_cursor("\n")
    app.home.viewer.insert_at_cursor(output)
    app.home.search_entry.set_text("> ")
    app.home.search_entry.set_position(2)


def engine_python(app, query):
    # try:
    #     if not hasattr(app.home, query):
    #         output = "doesn't have anything like that"
    # except
    output = "python engine not implemented"
    begin = app.home.viewer.textbuffer.get_start_iter()
    app.home.viewer.textbuffer.place_cursor(begin)
    app.home.viewer.insert_at_cursor("\n")
    app.home.viewer.insert_at_cursor(output)
    app.home.search_entry.set_text(">>> ")
    app.home.search_entry.set_position(4)


def plugin_main(app, fullpath):
    plugin_open_dir(app)
    plugin_open_src(app)
    app.home.engines.append((lambda q: q[0] == '$', lambda q: engine_shell(app.home, q[1:].strip())))
    app.home.engines.append((lambda q: q.startswith('>>>'), lambda q: engine_python(app, q[3:].strip())))
    app.home.engines.append((lambda q: q[0] == '>', lambda q: engine_cmd(app, q[1:].strip())))
    app.home.engines.append((lambda q: q.startswith('d:'), lambda q: engine_dump(app.home, q[2:].strip())))
    return True
