import asyncio
import logging

from common.databases import ra
from common.logger import setup_logging
from common.settings import CHECK_CONCURRENCY, REDIS_IP_QUEUE

setup_logging()
logger = logging.getLogger(__name__)


async def worker() -> None:
    while True:
        ip = (await ra.blpop(REDIS_IP_QUEUE))[1]
        print(ip)


async def main() -> None:
    tasks = [asyncio.create_task(worker()) for _ in range(CHECK_CONCURRENCY)]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
