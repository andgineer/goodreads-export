#!/usr/bin/env bash
# Recreate tests/resources using current version of the utility
rm -rf tests/resources/books/*
goodreads-export tests/resources/goodreads_library_export.csv -o tests/resources/books
