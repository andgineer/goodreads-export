#!/usr/bin/env bash
#
# Pin current dependencies versions.
#

rm -f requirements.txt
rm -f requirements.dev.txt

pip-compile requirements.dev.in
pip-compile requirements.in

# pip-compile ignores requrements specifiers, so we need to manually add them
echo 'tomli>=1.1.0; python_version < "3.11"' >> requirements.txt
