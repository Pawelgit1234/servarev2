import redis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from common.settings import DATABASE_URL, REDIS_HOST, REDIS_PORT

# Database
engine = create_async_engine(DATABASE_URL)
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
