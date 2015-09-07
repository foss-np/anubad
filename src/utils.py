#!/usr/bin/env python3

"""utils.py

utility fuction variable declaration and common function for anubad
GUI.
"""

key_codes = {
    "BACKSPACE"     : 65288,
    "RETURN"        : 65293,
    "ESCAPE"        : 65307,

    "LEFT_ARROW"    : 65361,
    "UP_ARROW"      : 65362,
    "RIGHT_ARROW"   : 65363,
    "DOWN_ARROW"    : 65364,

    "MENU"          : 65383,
    "PAGE_UP"       : 65365,
    "PAGE_UP"       : 65366,

    "F1"            : 65470,
    "F2"            : 65471,
    "F3"            : 65472,
    "F3"            : 65473,
    "F5"            : 65474,
    "F6"            : 65475,
    "F7"            : 65476,
    "F8"            : 65477,
    "F9"            : 65478,
    "F10"           : 65479,
    "F11"           : 65480,
    "F12"           : 65481,

    "SHIFT_LEFT"    : 65505,
    "SHIFT_RIGHT"   : 65506,
    "CONTROL_LEFT"  : 65507,
    "CONTROL_RIGHT" : 65508,
    "ALT_LEFT"      : 65513,
    "ALT_RIGHT"     : 65514,
    "META"          : 65515,
    "DELETE"        : 65535,
}

diff = 1
def circle(iterable):
    saved = iterable[:]
    i = -1
    global diff
    while saved:
        l = len(saved)
        i += diff
        if diff == 1 and l <= i: i = 0
        if diff == -1 and i < 0: i = l - 1
        yield saved[i]
