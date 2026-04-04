import redis

from common.settings import REDIS_HOST, REDIS_PORT

rs = redis.Redis(
    host=REDIS_HOST, port=REDIS_PORT, decode_responses=True
)  # sync
ra = redis.asyncio.Redis(
    host=REDIS_HOST, port=REDIS_PORT, decode_responses=True
)  # async
