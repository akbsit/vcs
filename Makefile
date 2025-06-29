default: sync

sync:
	poetry run python .scripts/sync.py

git:
	poetry run python .scripts/git.py

setup:
	poetry install --only main
