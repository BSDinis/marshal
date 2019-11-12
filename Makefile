BIN_DEST := ~/bin

CFLAGS = -Wall -Werror -Wreturn-type -Wundef -Wshadow \
				 -Wcast-align -Wcast-qual -Wconversion -Wredundant-decls \
				 -Winit-self -Wstrict-prototypes -pedantic -Wno-unused-variable \
				 -Wno-unused-function -Wsign-conversion -Wnull-dereference -Wdouble-promotion\
				 -Wformat=2

.PHONY: test
test:
	@cd test; \
	for f in $$(ls *.m); \
	do echo "running $$f"; \
	python3 ../scripts/marshal.py $$f -t; \
	clang $(CFLAGS) -fdiagnostics-color=always -c $${f%.m}.c -o $${f%.m}.o; \
	done; \
	cd ..

.PHONY: build
build: marshal

.PHONY: install
install: marshal
	cp marshal ${BIN_DEST}

marshal: scripts/*/*.py
	pyinstaller --onefile scripts/marshal.py
	cp dist/marshal .

