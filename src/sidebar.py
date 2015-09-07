#!/usr/bin/env python3

from gi.repository import Gtk
import utils

class Sidebar(Gtk.VBox):
    def __init__(self, parent=None):
        Gtk.HBox.__init__(self)
        self.parent = parent
        self.track_FONT = set()
        self.makeWidgets()


    def makeWidgets(self):
        self.pack_start(self.makeWidgets_treeview(), True, True, 0)
        self.track_FONT.add(self.treeview)
        self.treeview.connect("row-activated", self._on_row_double_click)
        treeselection = self.treeview.get_selection()
        treeselection.set_mode(Gtk.SelectionMode.MULTIPLE)
        self.select_signal = treeselection.connect("changed", self._on_row_changed)

        self.cb_filter = Gtk.ComboBoxText()
        self.pack_start(self.cb_filter, False, False, 0)
        self.cb_filter.append_text("All")
        self.cb_filter.set_active(0)


    def makeWidgets_treeview(self):
        scroll = Gtk.ScrolledWindow()
        scroll.set_hexpand(True)
        scroll.set_vexpand(True)

        self.treemodel = Gtk.ListStore(int, int, int, int, str, str)

        self.treeview = Gtk.TreeView(self.treemodel)
        scroll.add(self.treeview)

        self.treeview.set_headers_visible(False)
        self.treeview.set_rubber_banding(True)

        renderer_text = Gtk.CellRendererText()
        self.treeview.append_column(Gtk.TreeViewColumn("#", renderer_text, text=0))
        self.treeview.append_column(Gtk.TreeViewColumn("w", renderer_text, text=4))
        return scroll


    def _on_row_changed(self, treeselection):
        model, pathlist = treeselection.get_selected_rows()
        clip_out = []
        for path in pathlist:
            c, note, tab, ID, w, src = self.treemodel[path]
            note_obj = GUI.notebook_OBJS[note]
            browser_obj = note_obj.get_nth_page(tab)
            treerow = browser_obj.treebuffer[ID-1]
            meta = (note, tab, ID)
            view = meta not in self.parent.view_CURRENT
            clip_out += self.parent.viewer.parse(treerow, browser_obj.SRC, print_=view)
            self.parent.view_CURRENT.add(meta)

        if len(clip_out) > 0:
            GUI.clip_CYCLE = utils.circle(clip_out)
            self.parent._circular_search(+1)


    def _on_row_double_click(self, widget, treepath, treeviewcol):
        path, column = widget.get_cursor()
        # tab, obj, n, *row = self.items_FOUND[path[0]]
        # self.notebook.set_current_page(tab)
        # obj.treeview.set_cursor(n-1)


def treeview_signal_safe_toggler(func, ):
    '''Gtk.TreeView() :changed: signal should be disable before new
    selection is added, if connect it will trigger the change.

    '''
    def wrapper(self, *args, **kwargs):
        treeselection = self.sidebar.treeview.get_selection()
        treeselection.disconnect(self.sidebar.select_signal)
        func_return = func(self, *args, **kwargs)
        self.sidebar.select_signal = treeselection.connect("changed", self.sidebar._on_row_changed)
        return func_return
    return wrapper


def root_binds(widget, event):
    # print(event.keyval)
    if event.keyval == 65307:
        Gtk.main_quit()


def main():
    global root
    root = Gtk.Window()
    root.connect('delete-event', Gtk.main_quit)
    root.connect('key_release_event', root_binds)
    root.set_default_size(300, 200)

    sidebar = Sidebar(root)
    root.add(sidebar)

    return root

if __name__ == '__main__':
    main().show_all()
    Gtk.main()
