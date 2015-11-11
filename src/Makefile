NAME=`basename $(PWD)`

default: gtk3

demo: tk-py3

tk-py3: mysettings.conf
	python3 ./demo.pyw

tk-py2: mysettings.conf
	python2 demo.pyw

gtk3: mysettings.conf
	./app.py

debug:
	DEBUG=3 ./app.py

wine: mysettings.conf
	# note should load from same directory
	# and please set the python path in wine
	wine python demo.pyw

dist:
	rm -f "$(NAME).7z"
	7z a "$(NAME)" $(PWD)

mysettings.conf:
	touch mysettings.conf

core:
	./core.py

browser:
	./browser.py

viewer:
	./viewer.py

sidebar:
	./sidebar.py

add:
	./add.py

preference:
	./preferences.py

relations:
	./relations.py

wordnet:
	./wordnet.py ${WORD}
