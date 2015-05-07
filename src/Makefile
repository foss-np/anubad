NAME=`basename $(PWD)`

default: gtk3

tk-py: tk-py3

tk-py3: mysettings.conf
	python3 ./main.pyw

tk-py2: mysettings.conf
	python2 main.pyw

gtk3: mysettings.conf
	./main.py

wine: mysettings.conf
	# note should load from same directory
	# and please set the python path in wine
	wine python main.pyw

dist:
	rm -f "$(NAME).7z"
	7z a "$(NAME)" $(PWD)

browser:
	./browser.py

viewer:
	./viewer.py

add:
	./add.py

settings:
	./settings.py
