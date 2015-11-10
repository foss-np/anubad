#!/usr/bin/env python

from subprocess import Popen
from gi.repository import Gtk


def espeak(word, tone="nepali"):
    print("espeak:", word)
    Popen(["espeak", "-v", tone, word])


def plugin_main(root, fullpath):
    bar = root.toolbar
    bar.b_espeak = Gtk.ToolButton(icon_name=Gtk.STOCK_MEDIA_PLAY)
    bar.b_espeak.show()
    bar.insert(bar.b_espeak, 8)
    bar.b_espeak.connect("clicked", lambda w: espeak(root.copy_BUFFER))
    bar.b_espeak.set_tooltip_markup("Say it")
    return True
