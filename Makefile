
.PHONY: format lint typecheck test validate human-control-plane human-control-plane-check

format:
	ruff format src tests tools

lint:
	ruff check src tests tools

typecheck:
	mypy src

test:
	pytest -q

validate: lint typecheck test human-control-plane-check

human-control-plane:
	python tools/render_human_control_plane.py

human-control-plane-check:
	python tools/render_human_control_plane.py > /dev/null
