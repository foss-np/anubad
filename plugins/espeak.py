#!/usr/bin/env python

from subprocess import Popen
from gi.repository import Gtk


def espeak(word, tone="nepali"):
    print("espeak:", word)
    Popen(["espeak", "-v", tone, word])


def plugin_main(app, fullpath):
    b_ESPEAK = Gtk.ToolButton(icon_name=Gtk.STOCK_MEDIA_PLAY)
    app.insert_plugin_item_on_toolbar(b_ESPEAK)
    b_ESPEAK.set_tooltip_markup("Say it")
    b_ESPEAK.connect("clicked", lambda w: espeak(app.root.copy_buffer))
    b_ESPEAK.show()
    return True
