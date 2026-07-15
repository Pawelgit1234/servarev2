import logging

from common.databases import async_session, ra
from common.services.common import load_existing_entities, upload_servers
from common.services.server import get_ip, get_or_create_ip
from common.settings import REDIS_PORTER_QUEUE
from common.utils import normilize_ip, normilize_server_check

from checker.checks import check_server, check_server_ports
from checker.parsers import parse_masscan_address, parse_porter_address
from checker.services import (
    is_server_in_db,
    save_non_existing_servers,
    save_porter,
)
from checker.utils import extract_entities_from_checks

logger = logging.getLogger(__name__)


async def handle_masscan(address: str) -> None:
    masscan = parse_masscan_address(address)

    async with async_session() as db:  # type: ignore
        if await is_server_in_db(db, masscan.ip, masscan.port):
            return

        check = await check_server(masscan)
        if check is None:
            return

        server, ip_schema = check
        normilize_server_check(server)
        normilize_ip(ip_schema)

        await upload_servers([server])

        ip = await get_or_create_ip(db, ip_schema)
        entities = extract_entities_from_checks([server])
        entity_maps = await load_existing_entities(db, entities)

        save_non_existing_servers(db, [server], ip, entity_maps)
        await db.commit()

    logger.info(f"New server: {ip.ip}:{server.server.port}")

    if not masscan.is_multiport:
        await ra.rpush(REDIS_PORTER_QUEUE, ip.ip)  # type: ignore


async def handle_porter(address: str) -> None:
    ports, ip = parse_porter_address(address)
    defined_ports, servers = await check_server_ports(ports, ip)

    if not defined_ports and not servers:
        return

    async with async_session() as db:  # type: ignore
        ip_model = await get_ip(db, ip)

        # does not happen usually
        if ip_model is None:
            logger.warning(f"{ip} was not found in db")
            return

        for server in servers:
            normilize_server_check(server)

        await upload_servers(servers)

        await save_porter(db, defined_ports, servers, ip_model)
        await db.commit()

    logger.info(f"Ports and servers of {ip} were saved")
