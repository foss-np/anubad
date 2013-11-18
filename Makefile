NAME=`basename $(PWD)`

run:
	./main.py

py2:
	python2 main.py

cli:
	./main.py hello

dist:
	rm -f "$(NAME).7z"
	7z a "$(NAME)" $(PWD)
