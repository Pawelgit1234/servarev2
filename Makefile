lint:
	uv run ruff check .

format:
	uv run ruff format .

type:
	uv run mypy .

check:
	lint type

migrate:
	docker compose run --rm migrator alembic revision --autogenerate -m "$(name)"

upgrade:
	docker compose run --rm migrator alembic upgrade head

downgrade:
	docker compose run --rm migrator alembic downgrade -1