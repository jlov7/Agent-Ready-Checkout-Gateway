PYTHON ?= python
PIP ?= pip

.PHONY: install lint test format openapi seed

install:
	$(PIP) install ".[dev]"

lint:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ruff check .
	mypy .

test:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -p pytest_cov

openapi:
	$(PYTHON) scripts/export_openapi.py

seed:
	bash scripts/seed_demo.sh

demo:
	./scripts/run_demo.sh
