PYTHON ?= python3
PATHS = python-lib python-runnables tests scripts

.PHONY: check compile lint descriptors test

## Run every static check and the unit tests
check: compile lint descriptors test

compile:
	$(PYTHON) -m compileall -q $(PATHS)

lint:
	$(PYTHON) -m ruff check $(PATHS) --select F,E9
	$(PYTHON) -m pyflakes $(PATHS)

descriptors:
	$(PYTHON) scripts/check_descriptors.py

test:
	$(PYTHON) -m pytest -q tests
