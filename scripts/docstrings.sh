#!/usr/bin/env bash
#
# Extract docstrings to docs/
# make a copy for all languages
#

lazydocs \
    --output-path="./docs/docstrings" \
    --overview-file="index.md" \
    --src-base-url="https://github.com/andgineer/goodreads-export/blob/master/" \
    src/goodreads_export

mkdocs build --config-file docs/mkdocs-docstrings.yml
