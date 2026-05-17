import asyncio
import logging

from common.databases import async_session, ra
from common.logger import setup_logging
from common.session import session_manager
from common.settings import (
    CHECK_CONCURRENCY,
    REDIS_IP_QUEUE,
    REDIS_PORTER_QUEUE,
)

from checker.masscan import parse_masscan_address, process_masscan
from checker.porter import parse_porter_address, process_porter
from checker.services import (
    is_server_in_db,
    save_non_existing_server,
    save_ports,
)

setup_logging()
logger = logging.getLogger(__name__)


async def worker() -> None:
    while True:
        address: str = (await ra.blpop(REDIS_IP_QUEUE))[1]

        if address.startswith(REDIS_PORTER_QUEUE):
            ports, ip = parse_porter_address(address)
            defined_ports = await process_porter(ports, ip)

            async with async_session as db:
                await save_ports(db, *defined_ports, ip)
                await db.commit()
        else:
            masscan = parse_masscan_address(address)

            async with async_session as db:
                if await is_server_in_db(db, masscan.ip, masscan.port):
                    continue

                server = await process_masscan(address)
                if server is None:
                    continue

                await save_non_existing_server(db, server)
                await db.commit()

            logger.info(f"New server: {server.server.ip}:{server.server.port}")
            if not masscan.is_multiport:
                await ra.rpush(REDIS_PORTER_QUEUE, masscan.ip)


async def main() -> None:
    logger.info("Starts running")
    session_manager.init()
    workers = [asyncio.create_task(worker()) for _ in range(CHECK_CONCURRENCY)]
    await asyncio.gather(*workers)


if __name__ == "__main__":
    asyncio.run(main())
