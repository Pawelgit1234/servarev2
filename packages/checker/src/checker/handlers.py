import logging

from common.databases import async_session, ra
from common.logger import setup_logging
from common.services.server import upload_servers
from common.settings import REDIS_PORTER_QUEUE

from checker.checks import check_server, check_server_ports
from checker.parsers import parse_masscan_address, parse_porter_address
from checker.services import (
    is_server_in_db,
    save_non_existing_server,
    save_ports,
)

setup_logging()
logger = logging.getLogger(__name__)


async def handle_masscan(address: str) -> None:
    masscan = parse_masscan_address(address)

    async with async_session as db:  # type: ignore
        if await is_server_in_db(db, masscan.ip, masscan.port):
            return

        server = await check_server(masscan)
        if server is None:
            return

        await upload_servers([server])

        await save_non_existing_server(db, server)
        await db.commit()

    logger.info(f"New server: {server.server.ip}:{server.server.port}")

    if not masscan.is_multiport:
        await ra.rpush(REDIS_PORTER_QUEUE, masscan.ip)


async def handle_porter(address: str) -> None:
    ports, ip = parse_porter_address(address)
    defined_ports, servers = await check_server_ports(ports, ip)

    await upload_servers(servers)

    async with async_session as db:  # type: ignore
        await save_ports(db, defined_ports, servers, ip)
        await db.commit()

    logger.info(f"Ports and servers of {ip} were saved")
