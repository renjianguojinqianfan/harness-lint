.PHONY: verify test lint format-check install

verify: lint format-check test
	@echo "验证通过"

test:
	pytest tests/ -v --cov=src --cov-fail-under=85

lint:
	ruff check src/ tests/

format-check:
	ruff format --check src/

install:
	pip install -e ".[dev]"
