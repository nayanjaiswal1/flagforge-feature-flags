# FlagForge — Claude Code Instructions

## Environment
- Use the existing `venv/` virtual environment for all Python commands.
- Use `pnpm` for all Node/React package operations under `packages/`.

## Project Layout
- `src/flagforge/` — Python package (src layout, Python 3.10+)
- `packages/flagforge-react/` — TypeScript/React npm package
- `tests/` — pytest suite
- `docs/` — markdown documentation

## Commands
```bash
# Python
source venv/Scripts/activate       # Windows (bash)
pip install -e ".[all]"            # install all extras
pytest                             # run tests

# Node / React
cd packages/flagforge-react
pnpm install
pnpm build
pnpm test
```

## Code Style
- Python: follow existing ruff + mypy config in `pyproject.toml`
- TypeScript: follow existing tsconfig in `packages/flagforge-react/`
- Do not add comments or docstrings to code you didn't change.
- Keep changes minimal and focused on the task.

## Key Conventions
- Python union types: use `X | Y` syntax (Python 3.10+), not `Optional[X]`
- Use builtin generics: `list[str]`, `dict[str, int]` (not `List`, `Dict` from typing)
- Redis imports are lazy (via `__getattr__`) to avoid errors when redis extra is not installed
- YAML flag loader injects dict key as `flag_key` on each flag definition

## Testing
- Run `pytest` before committing changes
- All 33 existing tests must pass
- New features should include tests
