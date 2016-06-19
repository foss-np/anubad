#!/usr/bin/env python

from subprocess import Popen

def espeak(word, tone="nepali"):
    print("espeak:", word)
    Popen(["espeak", "-v", tone, word])


def plugin_main(app, fullpath):
    from gi.repository import Gtk

    b_ESPEAK = Gtk.ToggleToolButton(icon_name="media-playback-start")
    app.insert_plugin_item_on_toolbar(b_ESPEAK)
    b_ESPEAK.set_tooltip_markup("Say it")
    b_ESPEAK.connect("clicked", lambda w: espeak(app.home.copy_buffer))
    b_ESPEAK.show()
    return True


def sample():
    espeak("sample")


if __name__ == '__main__':
    sample()
