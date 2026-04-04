# Stage 1: Masscan
FROM ubuntu:22.04 AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
        git build-essential libpcap-dev ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/robertdavidgraham/masscan.git /masscan \
    && cd /masscan && make

# Stage 2: Scanner
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpcap0.8 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY packages/scanner/exclude.conf ./

COPY pyproject.toml uv.lock ./
COPY packages/common ./packages/common
COPY packages/scanner ./packages/scanner

RUN uv sync --frozen --package scanner --no-dev

COPY --from=builder /masscan/bin/masscan /usr/local/bin/masscan

CMD ["uv", "run", "--package", "scanner", "python", "-u", "-m", "scanner.main"]