#!/usr/bin/env python

from subprocess import Popen
from gi.repository import Gtk


def espeak(word, tone="nepali"):
    print("espeak:", word)
    Popen(["espeak", "-v", tone, word])


def plugin_main(app, fullpath):
    b_espeak = Gtk.ToolButton(icon_name=Gtk.STOCK_MEDIA_PLAY)
    app.insert_plugin_item_on_toolbar(b_espeak)
    b_espeak.set_tooltip_markup("Say it")
    b_espeak.connect("clicked", lambda w: espeak(app.root.copy_BUFFER))
    b_espeak.show()
    return True
