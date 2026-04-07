import os


def get_int(name: str) -> None | int:
    env = os.getenv(name)
    if env is not None:
        return int(env)
    return env


DATABASE_URL = (
    f"postgresql+asyncpg://{os.getenv('DB_USERNAME')}:"
    f"{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

REDIS_HOST = "redis"
REDIS_PORT = 6379

REDIS_IP_QUEUE = "ips"

MASSCAN_RATE = get_int("MASSCAN_RATE")
CHECK_CONCURRENCY = get_int("CHECK_CONCURRENCY")
