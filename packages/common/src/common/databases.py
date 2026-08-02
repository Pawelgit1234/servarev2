import redis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from common.settings import (
    DB_MAX_OVERFLOW,
    DB_POOL_SIZE,
    DB_POOL_TIMEOUT,
    DB_URL,
    REDIS_HOST,
    REDIS_PORT,
)

# Database
engine = create_async_engine(
    DB_URL,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_timeout=DB_POOL_TIMEOUT,
)
async_session = async_sessionmaker(
    engine, expire_on_commit=False, autoflush=False
)

# Redis
rs = redis.Redis(
    host=REDIS_HOST, port=REDIS_PORT, decode_responses=True
)  # sync
ra = redis.asyncio.Redis(
    host=REDIS_HOST, port=REDIS_PORT, decode_responses=True
)  # async
