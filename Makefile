NAME=`basename $(PWD)`

default: run

run:
	./main.pyw

py2:
	python2 main.pyw

cli:
	./main.pyw hello

gtk:
	./gtk3.py

wine:
	# note should load from same directory
	# and please set the python path in wine
	wine python main.pyw

dist:
	rm -f "$(NAME).7z"
	7z a "$(NAME)" $(PWD)

browser:
	./browselst.py

viewer:
	./viewer.py
