#!make
VERSION := $(shell cat src/goodreads_export/version.py | cut -d= -f2 | sed 's/\"//g; s/ //')
export VERSION

# If the first argument is "docs" treat additional "targets" as parameters
ifeq (docs,$(firstword $(MAKECMDGOALS)))
  DOCS_LANGUAGE := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  ifndef DOCS_LANGUAGE
    DOCS_LANGUAGE := en
  endif
  # turn the parameters into do-nothing targets
  $(eval $(RUN_ARGS):;@:)
endif

.HELP: version ## Show the current version
version:
	echo ${VERSION}

.HELP: ver-bug ## Bump the version for a bug
ver-bug:
	bash ./scripts/verup.sh bug

.HELP: ver-feature ## Bump the version for a feature
ver-feature:
	bash ./scripts/verup.sh feature

.HELP: ver-release ## Bump the version for a release
ver-release:
	bash ./scripts/verup.sh release

.HELP: reqs  ## Upgrade requirements including pre-commit
reqs:
	pre-commit autoupdate
	bash ./scripts/compile_requirements.sh
	pip install -r requirements.txt
	pip install -r requirements.dev.txt

.HELP: refresh ## Refresh test resources
refresh:
	bash ./scripts/refresh_test_resources.sh

.PHONY: docs # mark as phony so it always runs even we have a docs folder
.HELP: docs  ## Docs preview for the language specified (en ru), like "make docs ru", by default build for English
docs:
	bash ./scripts/docs-render-config.sh $(DOCS_LANGUAGE)
	open -a "Google Chrome" http://127.0.0.1:8000/goodreads-export/
	if [ $(DOCS_LANGUAGE) != "en" ]; then \
		cp -r ./docs/src/en/images/ ./docs/src/$(DOCS_LANGUAGE)/images/; \
	fi
	mkdocs serve -f docs/_mkdocs.yml

.HELP: help  ## Display this message
help:
	@grep -E \
		'^.HELP: .*?## .*$$' $(MAKEFILE_LIST) | \
		sort | \
		awk 'BEGIN {FS = ".HELP: |## "}; {printf "\033[36m%-19s\033[0m %s\n", $$2, $$3}'
