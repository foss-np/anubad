NAME=`basename $(PWD)`

run:
	./main.py

cli:
	./main.py hello

dist:
	rm -f "$(NAME).7z"
	7z a "$(NAME)" $(PWD)
