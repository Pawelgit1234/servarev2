import asyncio
import logging

from common.databases import engine
from common.logger import setup_logging
from common.session import session_manager
from common.settings import (
    MONITOR_PLAYER_CONCURRENCY,
    MONITOR_SERVER_CONCURRENCY,
)

from monitor.workers import player_worker, server_worker

setup_logging()
logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info("Starts running")
    session_manager.init()
    workers = [
        server_worker()
        for _ in range(MONITOR_SERVER_CONCURRENCY)  # type: ignore
    ] + [
        player_worker()
        for _ in range(MONITOR_PLAYER_CONCURRENCY)  # type: ignore
    ]

    try:
        await asyncio.gather(*workers)
    finally:
        logger.info("Shutting down")
        await engine.dispose()
        await session_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
