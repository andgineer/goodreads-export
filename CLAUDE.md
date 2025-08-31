# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python CLI tool that converts Goodreads book export CSV files into structured markdown files, optimized for use with Obsidian and other markdown-based applications. The tool processes book reviews, creates author files, handles series information, and uses Jinja2 templates for customizable output formatting.

## Development Environment Setup

Create and activate the development environment:
```bash
. ./activate.sh
```
This installs the package in editable mode and sets up the development environment.

## Core Commands

### Testing
```bash
pytest                    # Run all tests with doctest modules
pytest tests/test_*.py    # Run specific test files
```

### Code Quality and Linting
```bash
pre-commit install        # Install pre-commit hooks
pre-commit run --all-files # Run all pre-commit checks manually
mypy src/                 # Run type checking (mypy configured for src/ only)
ruff --fix --line-length=100 src/  # Run ruff linter with fixes
```

### Build and Package
```bash
pip install -e .          # Install in editable mode
python -m goodreads_export.main --help  # Test CLI installation
```

### Makefile Commands
```bash
make help                 # Show all available commands
make reqs                 # Upgrade requirements and pre-commit
make docs                 # Build and serve documentation
make refresh              # Refresh test resources
```

## Architecture Overview

### Core Components
- **CLI Interface** (`main.py`): Rich-click based command-line interface with subcommands for import, check, merge, and init
- **GoodreadsBooks** (`goodreads_book.py`): CSV parsing and book data extraction from Goodreads exports
- **Library** (`library.py`): Central orchestrator managing books, authors, and file operations
- **Templates** (`templates.py`): Jinja2 template loading and rendering system with built-in and custom template support
- **File Handlers**: Specialized classes for different markdown file types:
  - `book_file.py` - Individual book review files
  - `authored_file.py` - Author information files
  - `series_file.py` - Book series files

### Data Flow
1. CSV import via `GoodreadsBooks` class parses Goodreads export
2. `Library` class loads existing markdown files and merges with CSV data
3. Author name consolidation and deduplication occurs
4. Template system renders markdown files using Jinja2
5. Files are written to target directory with clean filename handling

### Template System
- Built-in templates included in package
- Custom templates can be loaded from filesystem
- Template consistency checking validates against extraction regexes
- Supports different template sets for various output formats

## Code Quality Configuration

- **Ruff**: Comprehensive linting with line length 100, extensive rule set including Pylint, Bugbear, Security, etc.
- **MyPy**: Type checking enabled for source code (excludes tests)
- **Pre-commit**: Automated checks on commit including YAML validation, whitespace cleanup, and code formatting
- **Testing**: pytest with doctest module support

## Entry Points

The package provides a console script:
- `goodreads-export` → `goodreads_export.main:main`

Available subcommands:
- `import` - Convert CSV to markdown files
- `check` - Validate template consistency
- `merge` - Merge duplicate authors
- `init` - Initialize template folder from built-ins
