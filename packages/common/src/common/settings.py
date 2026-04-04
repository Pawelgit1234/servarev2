import os


def get_int(name: str) -> None | int:
    env = os.getenv(name)
    if env is not None:
        return int(env)
    return env


REDIS_HOST = "redis"
REDIS_PORT = 6379

REDIS_IP_QUEUE = "ips"

MASSCAN_RATE = get_int("MASSCAN_RATE")
CHECK_CONCURRENCY = get_int("CHECK_CONCURRENCY")
