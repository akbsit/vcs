default: sync

provider ?=

sync:
	poetry run python .scripts/sync.py $(if $(provider),--provider $(provider),)

git:
	poetry run python .scripts/git.py $(if $(provider),--provider $(provider),)

setup:
	poetry install --only main
