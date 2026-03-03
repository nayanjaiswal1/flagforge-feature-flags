.PHONY: help install install-dev lint format typecheck test test-cov security audit clean

PYTHON := python
PIP    := pip
VENV   := venv

help:
	@echo "FlagForge development targets"
	@echo ""
	@echo "  install        Install package (core only)"
	@echo "  install-dev    Install package + all dev/extras"
	@echo "  lint           Run ruff linter"
	@echo "  format         Auto-format with ruff + black"
	@echo "  typecheck      Run mypy"
	@echo "  test           Run pytest"
	@echo "  test-cov       Run pytest with coverage report"
	@echo "  security       Run bandit SAST scan"
	@echo "  audit          Run pip-audit dependency scan"
	@echo "  secrets        Scan for accidentally committed secrets"
	@echo "  pre-commit     Run all pre-commit hooks"
	@echo "  clean          Remove build artefacts and caches"

install:
	$(PIP) install -e .

install-dev:
	$(PIP) install -e ".[dev,django,fastapi,redis]"
	$(PIP) install aiosqlite

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

typecheck:
	mypy src/flagforge --pretty --show-error-codes

test:
	pytest -q

test-cov:
	pytest --cov=flagforge --cov-report=term-missing --cov-report=html --cov-fail-under=80

security:
	bandit -r src/flagforge -c pyproject.toml -ll

audit:
	pip-audit -s osv

secrets:
	detect-secrets scan --baseline .secrets.baseline
	detect-secrets audit .secrets.baseline

pre-commit:
	pre-commit run --all-files

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "coverage.xml" -delete 2>/dev/null || true
	rm -rf htmlcov/ dist/ build/
