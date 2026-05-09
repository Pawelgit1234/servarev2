import asyncio
import logging

from common.checks.ip import get_ip_info
from common.databases import ra
from common.logger import setup_logging
from common.schemas.server import ServerPortSchema
from common.session import session_manager
from common.settings import (
    CHECK_CONCURRENCY,
    REDIS_IP_QUEUE,
    REDIS_PORTER_QUEUE,
)
from common.utils import merge_server_check_with_ip_info

from checker.check import check_server_by_protocol
from checker.masscan import parse_masscan_address
from checker.porter import parse_porter_address, scan_ports

setup_logging()
logger = logging.getLogger(__name__)


async def worker() -> None:
    while True:
        address: str = (await ra.blpop(REDIS_IP_QUEUE))[1]

        if address.startswith(REDIS_PORTER_QUEUE):
            ports, ip = parse_porter_address(address)
            responses = await scan_ports(ports, ip)

            print(
                [
                    r
                    for r in responses.values()
                    if isinstance(r, ServerPortSchema)
                ]
            )
        else:
            masscan = parse_masscan_address(address)

            # TODO: if server already in database: next ip
            #       but, will be redis faster? Or it is ok for db?

            server = await check_server_by_protocol(
                masscan.protocol, masscan.ip, masscan.port
            )
            if server is None:
                continue

            server.server.is_multiport = masscan.is_multiport

            ip_info = await get_ip_info(masscan.ip)
            if ip_info is None:
                # TODO: save to db, but save las_deep_check_at so, that monitor
                # will try again
                print(
                    f"{server.server.ip}:{server.server.port}",
                    f"{server.server_snapshot.motd}",
                    f"{server.server.country} ==== no ipinfo",
                )
                continue

            server = merge_server_check_with_ip_info(server, ip_info)

            if not masscan.is_multiport:
                await ra.rpush(REDIS_PORTER_QUEUE, masscan.ip)

            # TODO: db + set last_deep_check_at

            print(
                f"{server.server.ip}:{server.server.port}",
                f"{server.server_snapshot.motd}",
                f"{server.server.country}",
            )


async def main() -> None:
    logger.info("Starts running")
    session_manager.init()
    tasks = [asyncio.create_task(worker()) for _ in range(CHECK_CONCURRENCY)]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
