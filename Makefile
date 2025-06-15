default: sync

sync:
	poetry run python .scripts/sync.py

setup:
	poetry install --only main
