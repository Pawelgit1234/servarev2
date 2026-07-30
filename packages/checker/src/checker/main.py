import asyncio
import logging

from common.databases import engine, ra
from common.logger import setup_logging
from common.session import session_manager
from common.settings import CHECKER_WORKERS, REDIS_IP_QUEUE
from common.utils import restart_on_failure

from checker.handlers import handle_masscan, handle_porter

setup_logging()
logger = logging.getLogger(__name__)


@restart_on_failure(lambda worker_id: f"checker-worker-{worker_id}")  # type: ignore
async def worker(worker_id: int) -> None:
    while True:
        address: str = (await ra.blpop(REDIS_IP_QUEUE))[1]  # type: ignore

        if address.startswith("open"):
            await handle_masscan(address)
        else:
            await handle_porter(address)


async def main() -> None:
    logger.info("Starts running")
    session_manager.init()
    workers = [
        worker(i)
        for i in range(CHECKER_WORKERS)  # type: ignore
    ]

    try:
        await asyncio.gather(*workers)
    finally:
        logger.info("Shutting down")
        await engine.dispose()
        await ra.aclose()
        await session_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
