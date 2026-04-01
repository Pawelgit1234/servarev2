lint:
	uv run ruff check .

format:
	uv run ruff format .

type:
	uv run mypy .

check: lint type