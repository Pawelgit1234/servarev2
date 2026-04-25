import asyncio
import logging

from common.databases import ra
from common.logger import setup_logging
from common.settings import CHECK_CONCURRENCY, REDIS_IP_QUEUE

from checker.masscan import check_server_by_masscan, parse_masscan_address

setup_logging()
logger = logging.getLogger(__name__)


async def worker() -> None:
    while True:
        address = (await ra.blpop(REDIS_IP_QUEUE))[1]
        masscan = parse_masscan_address(address)
        server = await check_server_by_masscan(masscan)

        if server is not None:
            print(server.server_snapshot.motd)


async def main() -> None:
    logger.info("Starts running")
    tasks = [asyncio.create_task(worker()) for _ in range(CHECK_CONCURRENCY)]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
