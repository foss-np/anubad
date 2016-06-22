#!/usr/bin/env python3

"""
plugins specific to linux environment
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Notify', '0.7')
gi.require_version('Keybinder', '3.0')

from gi.repository import Gtk, Keybinder, Notify

from subprocess import Popen
from subprocess import check_output

notification = Notify.Notification()

def grab_notify(apps, *args):
    clip = check_output(["xclip", "-o"], universal_newlines=True)
    if clip is None: return
    query = clip.strip().lower()
    apps.home.search_entry.set_text(clip)
    apps.home.search_and_reflect()
    notifier(apps)


def notifier(app, *args):
    buffer = app.home.viewer.textbuffer

    insert = buffer.get_insert()
    beg    = buffer.get_start_iter()
    end    = buffer.get_iter_at_mark(insert)

    text   = buffer.get_text(beg, end, True)
    f_text = buffer.register_serialize_tagset(text)
    # buffer.serialize(buffer, format, beg, end)
    # print(text)
    # print(f_text)

    notification.update(text)
    #notification.update(text, body, icon)
    # notification.add_action(action, label, callback, *user_data)
    notification.show()

    xcowsay = app.plugins['xcowsay']
    xcowsay.popup(text)


def plugin_main(app, fullpath):
    Keybinder.init()
    Keybinder.bind("<Ctrl><Alt>v", lambda *a: grab_notify(app))
    Keybinder.bind("<Ctrl><Alt>m", lambda *a: notifier(app))
    Notify.init("anubad")
    notification.set_icon_from_pixbuf(app.pixbuf_logo)
    return True
