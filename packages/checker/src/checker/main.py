import asyncio
import logging

from common.databases import engine, ra
from common.logger import setup_logging
from common.session import session_manager
from common.settings import CHECK_CONCURRENCY, REDIS_IP_QUEUE

from checker.handlers import handle_masscan, handle_porter

setup_logging()
logger = logging.getLogger(__name__)


async def worker() -> None:
    while True:
        address: str = (await ra.blpop(REDIS_IP_QUEUE))[1]  # type: ignore

        if address.startswith("open"):
            await handle_masscan(address)
        else:
            await handle_porter(address)


async def main() -> None:
    logger.info("Starts running")
    session_manager.init()
    workers = [asyncio.create_task(worker()) for _ in range(CHECK_CONCURRENCY)]  # type: ignore

    try:
        await asyncio.gather(*workers)
    finally:
        logger.info("Shuting down")
        await engine.dispose()
        await ra.aclose()
        await session_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
