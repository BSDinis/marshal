BIN_DEST := ~/bin

.PHONY: test
test:
	@cd test; \
	for f in $$(ls *.m); \
	do echo "running $$f"; \
	python3 ../scripts/marshal.py $$f; \
	clang -Wall -Werror -pedantic -Wno-unused-function -fdiagnostics-color=always -c $${f%.m}.c -o $${f%.m}.o; \
	done; \
	cd ..

.PHONY: build
build: marshal

.PHONY: install
install: marshal
	cp marshal ${BIN_DEST}

marshal: scripts/marshal.py scripts/syntax/ast.py scripts/lex/scanner.py scripts/visit/visit_c_header.py scripts/visit/helpers.py scripts/visit/visit_c_code.py scripts/visit/visit_c_prot.py
	pyinstaller --onefile scripts/marshal.py
	cp dist/marshal .

