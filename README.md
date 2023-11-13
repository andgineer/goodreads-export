[![Build Status](https://github.com/andgineer/goodreads-export/workflows/Test/badge.svg)](https://github.com/andgineer/goodreads-export/actions)
[![Coverage](https://raw.githubusercontent.com/andgineer/goodreads-export/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/andgineer/goodreads-export/blob/python-coverage-comment-action-data/htmlcov/index.html)
# Export goodreads books into markdown files (Obsidian etc)

![goodreads.png](https://andgineer.github.io/goodreads-export/en/goodreads.png)
![goodreads-author.png](https://andgineer.github.io/goodreads-export/en/goodreads-author.png)

# User manual

[goodreads-export](https://andgineer.github.io/goodreads-export/en/)

# Developers
### Codebase structure
[Auto-generated reference](https://andgineer.github.io/goodreads-export/docstrings/).

### Create / activate environment
    . ./activate.sh

It will also install the package in [edit mode](https://realpython.com/what-is-pip/#installing-packages-in-editable-mode-to-ease-development).

### Setting Up Pre-commit for Formatting and Static Checks

1. **Install Pre-commit**:
   ```bash
   pip install pre-commit
   ```

2. **Configure Pre-commit**:
   ```bash
   pre-commit install
   ```

This sets up `pre-commit` in your local environment to run the same static checks as the `static` GitHub Action.

### Scripts
    make help

## Coverage report
* [Codecov](https://app.codecov.io/gh/andgineer/goodreads-export/tree/main/src%2Fgoodreads_export)
* [Coveralls](https://coveralls.io/github/andgineer/goodreads-export)
