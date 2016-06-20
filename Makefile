PKG_NAME = anubad

default: app

app:
	cd src; make

unlink:
	rm -f /usr/local/bin/${PKG_NAME}

link: unlink
	ln -s "$(PWD)/src/main.py" /usr/local/bin/${PKG_NAME}

demo: tk-py3

tk-py3:
	python3 demo.pyw

tk-py2:
	python2 demo.pyw
