#!/usr/bin/env bash
# Recreate tests/resources using current version of the utility
# set -evx  # uncomment for debugging
for testcase in tests/resources/*/; do
  rm -rf ${testcase}books/*
  cp -r ${testcase}existed/ ${testcase}books
  goodreads-export import ${testcase}books -i ${testcase}goodreads_library_export.csv
done
