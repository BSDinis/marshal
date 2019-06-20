BIN_DEST := ~/bin

.PHONY: test
test:
	@for f in $$(ls test/*.m); \
	do echo "running $$f"; \
	python3 scripts/marshal.py $$f; \
	done;

.PHONY: build
build: marshal

.PHONY: install
install: marshal
	cp marshal ${BIN_DEST}

marshal: scripts/marshal.py scripts/syntax/ast.py scripts/lex/scanner.py scripts/visit/visit_c_header.py scripts/visit/helpers.py scripts/visit/visit_c_code.py scripts/visit/visit_c_prot.py
	pyinstaller --onefile scripts/marshal.py
	cp dist/marshal .

