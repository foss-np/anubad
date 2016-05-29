NAME=`basename $(PWD)`

default: all

all:
	./main.py

verbose3:
	VERBOSE=3 ./main.py

verbose4:
	VERBOSE=4 ./main.py

dist:
	rm -f "$(NAME).7z"
	7z a "$(NAME)" $(PWD)

mysettings.conf:
	touch mysettings.conf

core:
	./core.py

config-test:
	./config.py
