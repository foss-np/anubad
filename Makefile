NAME=`basename $(PWD)`

default: gtk

py: py3

py3: mysettings.conf
	./main.pyw

py2: mysettings.conf
	python2 main.pyw

cli: mysettings.conf
	./main.pyw hello

gtk: mysettings.conf
	./gtk3.py

wine: mysettings.conf
	# note should load from same directory
	# and please set the python path in wine
	wine python main.pyw

dist:
	rm -f "$(NAME).7z"
	7z a "$(NAME)" $(PWD)

browser:
	./browselst.py

browser2:
	./browselst2.py

viewer:
	./viewer.py

viewer2:
	./viewer2.py
