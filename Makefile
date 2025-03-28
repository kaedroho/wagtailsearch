.PHONY: lint

lint:
	ruff format
	ruff check --select I --fix
	ruff check --fix
	ruff format
