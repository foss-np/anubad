NAME=`basename $(PWD)`

default: all

all:
	./main.py

debug:
	DEBUG=3 ./main.py

dist:
	rm -f "$(NAME).7z"
	7z a "$(NAME)" $(PWD)

mysettings.conf:
	touch mysettings.conf

core:
	./core.py

distance:
	./distance.py

config-test:
	./config.py
