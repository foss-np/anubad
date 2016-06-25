#!/usr/bin/env python3

"""tricks for power users


Collection of extra functionality and fancy tricks, for developers,
and power users, not really required plugins.

"""

__platform__ = 'posix'
__version__  = '0.1'
__authors__  = 'rho'
__support__  = 'https://github.com/foss-np/anubad/'

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk

import os
import linecache
from subprocess import Popen
from subprocess import check_output

def plugin_open_dir(app):
    b_OPEN = Gtk.ToolButton(icon_name="folder")
    app.insert_plugin_item_on_toolbar(b_OPEN)
    b_OPEN.set_tooltip_markup("Open Glossary Directory")

    def _browse(*arg):
        app.home.toolbar.t_COPY.set_active(False)
        dialog = Gtk.Dialog(parent = app.home)

        for i, gloss in enumerate(app.cnf.glossary_list):
            dialog.add_button(gloss['name'], i)

        dialog.connect( # quit when Esc is pressed
            'key_press_event',
            lambda w, e: dialog.destroy() if e.keyval == 65307 else None
        )

        dialog.connect(
            "response",
            lambda w, _id: print(
                "pid:",
                Popen([
                    app.cnf.apps['file-manager'],
                    app.cnf.glossary_list[_id]["path"]
                ]).pid
            )
        )
        dialog.run()
        dialog.destroy()

    b_OPEN.connect("clicked", _browse)
    b_OPEN.show()


def plugin_open_src(app):
    def _edit():
        app.home.toolbar.t_COPY.set_active(False)
        treeSelection = app.home.sidebar.treeview.get_selection()
        model, pathlst = treeSelection.get_selected_rows()

        if len(pathlst) == 0:
            path  = app.cnf.glossary_list[0]['pairs'][0]
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
    home.searchbar.entry.set_text("$ ")
    home.searchbar.entry.set_position(2)
    try:
        output = check_output(query.split(), universal_newlines=True)
    except:
        return

    return output


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



def plugin_main(app, fullpath):
    plugin_open_dir(app)
    plugin_open_src(app)
    app.home.engines.append((lambda q: q[0] == '$', lambda q: engine_shell(app.home, q[1:].strip())))
    app.home.engines.append((lambda q: q.startswith('d:'), lambda q: engine_dump(app.home, q[2:].strip())))
