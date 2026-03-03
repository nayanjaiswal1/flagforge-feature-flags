# Contributing to FlagForge

Thank you for your interest in contributing! This document covers how to set up the project locally, run tests, and submit changes.

---

## Development Setup

### Prerequisites

- Python 3.10+
- `venv` (standard library)
- PostgreSQL (optional, for integration tests)
- Redis (optional, for cache backend tests)

### Clone and install

```bash
git clone https://github.com/flagforge/flagforge.git
cd flagforge

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -e ".[dev,django,fastapi,redis]"
```

### Pre-commit hooks

```bash
pre-commit install
```

---

## Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=flagforge --cov-report=term-missing

# Specific module
pytest tests/test_engine.py

# Django tests only
pytest tests/django/

# FastAPI tests only
pytest tests/fastapi/
```

---

## Linting and Type Checking

```bash
# Lint
ruff check src/

# Format check
black --check src/

# Type check
mypy src/
```

---

## Project Structure

```
src/flagforge/
├── core/
│   ├── engine.py       # FlagEngine, AsyncFlagEngine
│   ├── resolver.py     # Resolution logic (priority chain)
│   ├── hasher.py       # MurmurHash3 bucketing
│   ├── context.py      # FeatureContext, request_context
│   ├── models.py       # FlagDefinition, TenantOverride dataclasses
│   └── exceptions.py
├── storage/
│   ├── base.py         # Abstract StorageBackend interfaces
│   ├── memory.py       # InMemoryStorage, AsyncInMemoryStorage
│   └── yaml_loader.py  # YAML file loader and sync
├── cache/
│   ├── base.py         # Abstract CacheBackend interfaces
│   ├── local.py        # LocalCache, AsyncLocalCache
│   ├── redis.py        # RedisCache, AsyncRedisCache
│   ├── null.py         # NullCache, AsyncNullCache
│   └── keys.py         # Cache key utilities
├── contrib/
│   ├── django/         # Django app
│   └── fastapi/        # FastAPI integration
└── cli/
    └── main.py         # Click CLI
```

---

## Guidelines

- **Keep changes focused** — one feature or bug fix per PR
- **Add tests** — all new code should have tests
- **Type hints** — new functions should have type annotations
- **No breaking changes** in minor versions
- **Update CHANGELOG.md** for user-facing changes

---

## Submitting a PR

1. Fork the repository
2. Create a branch: `git checkout -b feature/my-feature`
3. Make changes and add tests
4. Run `pytest` and `ruff check` — ensure they pass
5. Push and open a Pull Request against `main`

---

## Reporting Issues

Use [GitHub Issues](https://github.com/flagforge/flagforge/issues). Please include:

- Python version
- FlagForge version (`pip show flagforge`)
- Minimal reproduction code
- Full traceback if applicable
