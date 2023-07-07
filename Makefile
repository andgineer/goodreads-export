#!make
VERSION := $(shell cat src/goodreads_export/version.py | cut -d= -f2 | sed 's/\"//g; s/ //')
export VERSION

version:
	echo ${VERSION}

ver-bug:
	bash ./scripts/verup.sh bug

ver-feature:
	bash ./scripts/verup.sh feature

ver-release:
	bash ./scripts/verup.sh release

reqs:
	pre-commit autoupdate
	bash ./scripts/compile_requirements.sh
	pip install -r requirements.txt
	pip install -r requirements.dev.txt

refresh:
	bash ./scripts/refresh_test_resources.sh
