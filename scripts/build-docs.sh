#!/usr/bin/env bash
#
# Create docs in docs/
#

lazydocs \
    --output-path="./docs/docstrings" \
    --overview-file="README.md" \
    --src-base-url="https://github.com/andgineer/goodreads-export/blob/master/" \
    src/goodreads_export

mkdocs build
