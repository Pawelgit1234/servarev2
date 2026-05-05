#!/usr/bin/env bash
set -e

export DISABLE_DOCKER=1
export DB_HOST=localhost
export DB_PORT=5432

docker compose up --build &

SCANNER_PID=""
PORTER_PID=""

cleanup() {
  echo "Stopping services..."

  kill $SCANNER_PID $PORTER_PID 2>/dev/null || true
  wait 2>/dev/null || true

  exit 0
}

trap cleanup INT TERM EXIT

uv run --env-file .env --package scanner python -u -m scanner.main & # ?
# uv run --env-file .env -m scanner.main &
SCANNER_PID=$!

uv run --env-file .env --package scanner python -u -m porter.main & # ?
# uv run --env-file .env -m porter.main &
PORTER_PID=$!

wait