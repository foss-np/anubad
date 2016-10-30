#!/usr/bin/env python3

"""tricks for power users


Collection of extra functionality and fancy tricks, for developers,
and power users, not really required plugins.

"""

__platform__ = 'posix'
__version__  = 0.3
__authors__  = 'rho'
__support__  = 'https://github.com/foss-np/anubad/'

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk

import os
import linecache
from subprocess import Popen
from subprocess import check_output


def browse_gloss(app):
    dialog = Gtk.MessageDialog(transient_for=app.home)

    dialog.props.text = 'Double Click on row to open'
    layout = dialog.get_content_area()

    scroll = Gtk.ScrolledWindow()
    layout.add(scroll)
    scroll.set_min_content_height(220)
    scroll.set_min_content_width(380)

    treemodel = Gtk.TreeStore(str, str, int)
    for key, instance in app.home.core.Glossary.instances.items():
        root = treemodel.append(None, ["folder", key, instance.counter])
        for _file in instance:
            treemodel.append(root, ["text-x-generic", _file, len(instance[_file][0])])


    treeview = Gtk.TreeView(treemodel)
    scroll.add(treeview)

    def _on_row_activate(widget, treepath, treecol):
        model    = widget.get_model()
        treeiter = model.get_iter(treepath)
        path     = model.get_value(treeiter, 1)
        parent   = model.iter_parent(treeiter)
        dialog.destroy()
        if parent:
            path = model.get_value(parent, 1) + path
            print(Popen([app.cnf.apps['editor'], path]).pid)
            return

        print(Popen([app.cnf.apps['file-manager'], path]).pid)

    treeview.append_column(Gtk.TreeViewColumn("image", Gtk.CellRendererPixbuf(), icon_name=0))
    treeview.append_column(Gtk.TreeViewColumn("gloss", Gtk.CellRendererText(), text=1))
    treeview.append_column(Gtk.TreeViewColumn("count", Gtk.CellRendererText(), text=2))
    treeview.expand_all()
    treeview.set_headers_visible(False)
    treeview.set_search_column(1)
    treeview.connect("row-activated", _on_row_activate)

    layout.show_all()
    dialog.run()
    dialog.destroy()


def addPlugin_open_dir(app):
    def _on_key_release(widget, event):
        if Gdk.ModifierType.MOD1_MASK & event.state:
            if event.keyval == ord('o'): browse_gloss(app)

    app.home.connect('key_release_event', _on_key_release)

    b_OPEN = Gtk.ToolButton(icon_name="folder")
    app.home.insert_plugin_item_on_toolbar(b_OPEN)
    b_OPEN.set_tooltip_markup("Open Glossary Directory")
    b_OPEN.connect("clicked", lambda *a: browse_gloss(app))
    b_OPEN.show()


def addPlugin_open_src(app):
    def _edit():
        app.home.toolbar.t_COPY.set_active(False)
        treeSelection = app.home.sidebar.treeview.get_selection()
        model, pathlst = treeSelection.get_selected_rows()

        if len(pathlst) == 0: browse_gloss(app); return
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


def addEngine_shell(ui):
    def piston(query):
        ui.searchbar.entry.set_text("$ ")
        ui.searchbar.entry.set_position(2)
        try:
            # TODO handle error, exit != 0
            output = check_output(query.split(), universal_newlines=True)
        except:
            return
        return output

    engine = {
        'name'   : "shell",
        'filter' : lambda q: q[0] == '$',
        'piston' : lambda q: piston(q[1:]),
        'shaft'  : lambda a: ui.fit_output(a),
    }
    ui.search_engines.append(engine)



def plugin_main(app, fullpath):
    addPlugin_open_dir(app)
    addPlugin_open_src(app)
    addEngine_shell(app.home)
