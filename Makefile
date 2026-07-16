
.PHONY: format lint typecheck test validate

format:
	ruff format src tests

lint:
	ruff check src tests

typecheck:
	mypy src

test:
	pytest -q

validate: lint typecheck test
