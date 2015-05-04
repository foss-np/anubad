NAME=`basename $(PWD)`

default: gtk3

tk-py: tk-py3

tk-py3: mysettings.conf
	./main.pyw

tk-py2: mysettings.conf
	python2 main.pyw

cli: mysettings.conf
	./main.pyw hello

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
	./browselst.py

browser2:
	./browselst2.py

viewer:
	./viewer.py

viewer2:
	./viewer2.py

add:
	./add.py
