lint:
	uv run ruff check .

format:
	uv run ruff format .

type:
	uv run mypy .

check:
	lint type

migrate:
	docker compose run --rm --build migrator alembic revision --autogenerate -m "$(name)"

upgrade:
	docker compose run --rm --build migrator alembic upgrade head

drizzle-pull:
	docker compose run --rm bot npm run db:pull
	docker compose stop db

downgrade:
	docker compose run --rm --build migrator alembic downgrade -1

test:
	docker compose run --rm --build tester || true
	docker compose stop db_test