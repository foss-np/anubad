NAME=`basename $(PWD)`

run:
	./main.pyw

py2:
	python2 main.pyw

cli:
	./main.pyw hello

dist:
	rm -f "$(NAME).7z"
	7z a "$(NAME)" $(PWD)
