# Repository Guidelines

## Project Structure & Module Organization
- Source: `src/goodreads_export/` (CLI in `main.py`, core in `library.py`, parsing in `goodreads_book.py`, templates in `templates.py` and `templates/`).
- Tests: `tests/` with fixtures in `tests/conftest.py` and sample data under `tests/resources/`.
- Docs: `docs/` (MkDocs); helper scripts in `scripts/`.
- Entry point: console script `goodreads-export` (see `setup.py`).

## Build, Test, and Development Commands
- Create/activate env: `. ./activate.sh` (uses uv; installs dev deps and the package editable).
- Lint/format locally: `pre-commit install` then `pre-commit run -a`.
- Run tests: `pytest -q` or with coverage `pytest -q --cov=goodreads_export`.
- Docs: `make docs` (builds and serves MkDocs), `make docs-src` (docstrings site).
- Version bump (maintainers): `make ver-bug|ver-feature|ver-release`.
- Useful: `make help` to list available targets.

## Coding Style & Naming Conventions
- Language: Python 3.9+ (dev uses 3.12). Use type hints throughout.
- Indent with 4 spaces; target line length 100.
- Names: modules/files `snake_case.py`, functions/variables `snake_case`, classes `PascalCase`.
- Tools: Ruff (lint + format), MyPy (types). Flake8/pylint config exists for CI parity.

## Testing Guidelines
- Framework: Pytest with doctests enabled (`pytest.ini` sets `--doctest-modules`).
- Place tests in `tests/test_*.py`; mirror module names where possible.
- Use resources under `tests/resources/`; refresh via `make refresh` when fixtures change.
- Aim to keep coverage stable or increasing; prefer unit-level tests near changed code.

## Commit & Pull Request Guidelines
- Messages: concise, imperative (“Add X”, “Fix Y”); reference issues (`#123` or link). No strict conventional-commits in history.
- PRs: include a clear description, linked issues, and before/after notes for CLI or docs changes; add/adjust tests and docs.
- Hygiene: run `pre-commit run -a` and `pytest` locally; ensure CI is green. Do not commit personal Goodreads exports.
- Versioning: do not hand-edit versions; maintainers use `make ver-*` which tags and updates `src/goodreads_export/version.py`.

## Security & Configuration Tips
- The tool operates on exported CSVs; avoid committing real user data. Use `tests/resources/` for examples.
- CLI examples:
  - Import: `goodreads-export import ./books -i ./goodreads_library_export.csv`
  - Check templates: `goodreads-export check -t ./templates`
  - Init templates: `goodreads-export init ./books -t ./templates -b default`
