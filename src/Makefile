SOURCES = $(wildcard *.py) #src/ui/*.py src/ui/*.css
SUPPORT = README.org AUTHORS LICENSE assets/wiki.svg
PKG_NAME = anubad
FILE_CONFIG="${HOME}/.cache/default.ini"

PKG_NAME = anubad

default: all

all:
	./main.py

verbose3:
	VERBOSE=3 ./main.py

verbose4:
	VERBOSE=4 ./main.py

core:
	./core.py

setting:
	./setting.py

commander:
	./commander.py

utils:
	./utils.py

unlink:
	rm -f /usr/local/bin/${PKG_NAME}

link: unlink
	ln -s "$(PWD)/main.py" /usr/local/bin/${PKG_NAME}

gtk-lt-12-patch:
	sed -i 's/Gtk.Popover/Gtk.Dialog/' ui/_searchbar.py
	sed -i '/relative_to/d' ui/_searchbar.py
	sed -i '/self.connect("closed"/d' ui/_searchbar.py
	sed -i 's/layout = Gtk.Box.*/layout = self.get_content_area()/' ui/_searchbar.py

