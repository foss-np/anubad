#!/usr/bin/env python

from subprocess import Popen
from gi.repository import Gtk


def espeak(word):
    print("espeak:", Popen(["espeak", "-v", "nepali", word]).pid)


def plugin_main(root, fullpath):
    bar = root.toolbar
    bar.b_espeak = Gtk.ToolButton(icon_name=Gtk.STOCK_MEDIA_PLAY)
    bar.b_espeak.show()
    bar.insert(bar.b_espeak, 8)
    bar.b_espeak.connect("clicked", lambda w: espeak(root.copy_BUFFER))
    bar.b_espeak.set_tooltip_markup("Say the Word")
    return True
