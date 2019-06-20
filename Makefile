.PHONY: test
test:
	@for f in $$(ls test/*.m); \
	do echo "running $$f"; \
	python3 scripts/marshal.py $$f; \
	done;

.PHONY: build
build:
	pyinstaller --onefile scripts/marshal.py
	cp dist/marshal .
