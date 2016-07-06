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
