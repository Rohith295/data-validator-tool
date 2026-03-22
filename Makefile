VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
MIN_PYTHON := 3.10
PY_VERSIONS := 3.11 3.12 3.13

.PHONY: setup test test-e2e lint format typecheck tox all clean samples check-python build setup-pythons

check-python:
	@python3 -c "import sys; v=sys.version_info; exit(0 if (v.major,v.minor)>=(3,10) else 1)" \
		|| (echo "Error: Python >= $(MIN_PYTHON) required, found $$(python3 --version)" && exit 1)

setup-pythons:
	@command -v pyenv >/dev/null 2>&1 || (echo "Error: pyenv is required. Install from https://github.com/pyenv/pyenv" && exit 1)
	@for v in $(PY_VERSIONS); do \
		if ! pyenv versions --bare | grep -q "^$$v"; then \
			echo "==> Installing Python $$v via pyenv..."; \
			pyenv install -s $$v:latest; \
		fi; \
	done
	@echo "==> Setting pyenv local versions..."
	@pyenv local $$(for v in $(PY_VERSIONS); do pyenv versions --bare | grep "^$$v" | tail -1; done)

$(VENV)/bin/activate: check-python
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip

setup: $(VENV)/bin/activate
	$(PIP) install -e ".[dev]"
	$(PIP) install tox

test: $(VENV)/bin/activate
	$(PYTHON) -m pytest tests/ --ignore=tests/e2e -v --cov=data_validator --cov-report=term-missing

test-e2e: $(VENV)/bin/activate setup-pythons
	$(VENV)/bin/tox -e 'e2e-py{311,312,313}'

samples: $(VENV)/bin/activate
	./run_samples.sh

lint: $(VENV)/bin/activate
	$(VENV)/bin/ruff check src/ tests/

format: $(VENV)/bin/activate
	$(VENV)/bin/ruff format src/ tests/

typecheck: $(VENV)/bin/activate
	$(VENV)/bin/mypy src/

build: $(VENV)/bin/activate
	$(PIP) install build
	$(VENV)/bin/python -m build

tox: $(VENV)/bin/activate setup-pythons
	$(VENV)/bin/tox

all: lint typecheck test test-e2e

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .mypy_cache .ruff_cache .pytest_cache htmlcov .coverage dist build .tox

nuke: clean
	rm -rf $(VENV)
