PYTHON ?= python3
PATHS = python-lib python-runnables resource tests scripts
# webapps/*/backend.py uses the `app` object DSS injects; ruff honours the noqa, pyflakes does not
WEBAPP_PATHS = webapps

.PHONY: check compile lint descriptors test

## Run every static check and the unit tests
check: compile lint descriptors test

compile:
	$(PYTHON) -m compileall -q $(PATHS) $(WEBAPP_PATHS)

lint:
	$(PYTHON) -m ruff check $(PATHS) $(WEBAPP_PATHS) --select F,E9
	$(PYTHON) -m pyflakes $(PATHS)

descriptors:
	$(PYTHON) scripts/check_descriptors.py

test:
	$(PYTHON) -m pytest -q tests
