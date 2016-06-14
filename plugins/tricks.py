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

import setting

def plugin_open_dir(app):
    b_OPEN = Gtk.ToolButton(icon_name=Gtk.STOCK_OPEN)
    app.insert_plugin_item_on_toolbar(b_OPEN)
    b_OPEN.set_tooltip_markup("Open Glossary Directory")

    def _browse(*arg):
        app.home.toolbar.t_COPY.set_active(False)
        path  = app.cnf.glossary_list['foss']['pairs'][0]
        explorer = app.cnf.apps['file-manager']
        print("pid:", Popen([explorer, path]).pid)

    b_OPEN.connect("clicked", _browse)
    b_OPEN.show()


def plugin_open_src(app):
    def _edit():
        app.home.toolbar.t_COPY.set_active(False)
        treeSelection = app.home.sidebar.treeview.get_selection()
        model, pathlst = treeSelection.get_selected_rows()

        if len(pathlst) == 0:
            path  = app.cnf.glossary_list['foss']['pairs'][0]
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

        cmd = app.cnf.editor_goto_line_uri(src, line)
        print("pid:", src, Popen(cmd).pid)

    def _on_key_release(widget, event):
        if Gdk.ModifierType.MOD1_MASK & event.state:
            if event.keyval == ord('e'): _edit()

    app.home.connect('key_release_event', _on_key_release)


def engine_shell(home, query):
    # TODO handle error, exit != 0
    home.search_entry.set_text("$ ")
    home.search_entry.set_position(2)
    return check_output(query.split(), universal_newlines=True)



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

    return output

def engine_python(app, query):
    # try:
    #     if not hasattr(app.home, query):
    #         output = "doesn't have anything like that"
    # except
    app.home.search_entry.set_text(">>> ")
    app.home.search_entry.set_position(4)
    return "python engine not implemented"


def plugin_main(app, fullpath):
    plugin_open_dir(app)
    plugin_open_src(app)
    app.home.engines.insert(0, ((lambda q: q.startswith('>>>'), lambda q: engine_python(app, q[3:].strip()))))
    app.home.engines.append((lambda q: q[0] == '$', lambda q: engine_shell(app.home, q[1:].strip())))
    app.home.engines.append((lambda q: q.startswith('d:'), lambda q: engine_dump(app.home, q[2:].strip())))
    return True
