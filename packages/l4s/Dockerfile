FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
COPY packages/common ./packages/common
COPY packages/l4s ./packages/l4s

RUN uv sync --frozen --package l4s --no-dev

CMD ["uv", "run", "--package", "l4s", "python", "-u", "-m", "l4s.main"]
