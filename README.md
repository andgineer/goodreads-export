[![Build Status](https://github.com/andgineer/goodreads-export/workflows/ci/badge.svg)](https://github.com/andgineer/goodreads-export/actions)
# Export goodreads books into markdown files (Obsidian etc)

![goodreads.png](docs%2Fgoodreads.png)
![goodreads-author.png](docs%2Fgoodreads-author.png)

# Documentation

[goodreads-export](https://andgineer.github.io/goodreads-export/)

# Developers

#### Create / activate environment
    . ./activate.sh

Delete `venv/` if you want to reinstall everything from requirements*.txt

    make reqs  # if you want to refresh versions
    deactivate
    rm -f venv
    pip install --upgrade pip-tools
    . ./activate.sh

#### Compile pinned to versions requirements*.txt from requirements*.in files

Using pip-tools

    make reqs

#### Release version
    make ver-bug/feature/release

Github actin will automatically update the pip package on pypi.org

# Docstrings documentation

Documentation generated from source code.

[reference](docstrings/)
