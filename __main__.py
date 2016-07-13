#!/usr/bin/env python3
"""
packaged
"""

import src.main

# TODO wrap streams
import pkg_resources
# print(pkg_resources.resource_string(__name__, 'AUTHORS'))
# print(pkg_resources.resource_string(__name__, 'home.css'))
# pkg_resources.resource_stream('app', 'wiki.svg')

if __name__ == '__main__':
    app, commands = src.main.main()
    app.run(commands)
