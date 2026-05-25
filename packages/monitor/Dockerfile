FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
COPY packages/common ./packages/common
COPY packages/monitor ./packages/monitor

RUN uv sync --frozen --package monitor --no-dev

CMD ["uv", "run", "--package", "monitor", "python", "-u", "-m", "monitor.main"]