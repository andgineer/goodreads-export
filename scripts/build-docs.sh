#!/usr/bin/env bash
#
# Create docs in docs/
#

rm -rf site

./scripts/docstrings.sh

mkdocs build --dirty --config-file docs/mkdocs-en.yml
# mkdocs build --dirty --config-file docs/mkdocs-ru.yml
