.PHONY: test
test:
	@for f in $$(ls test/*.m); \
	do echo "running $$f"; \
	./marshal $$f; \
	done;

.PHONY: install
install:
