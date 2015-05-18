ms-win:
	git stash
	sed -i 's/(icon_name=/.new_from_stock(/p' src/*.py
	touch mswin
	cd src; make

restore: mswin
	rm mswin
	git reset --hard HEAD
	cd src; make
