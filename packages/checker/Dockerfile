FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
COPY packages/common ./packages/common
COPY packages/checker ./packages/checker

RUN uv sync --frozen --package checker --no-dev

CMD ["uv", "run", "--package", "checker", "python", "-u", "-m", "checker.main"]