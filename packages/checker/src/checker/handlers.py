import logging

from common.checks.ip import get_ip_info
from common.databases import async_session, ra
from common.schemas.ip import IpInfoSchema
from common.services.common import upload_servers
from common.services.entities import load_existing_entities
from common.services.server import create_ip, get_ip
from common.settings import REDIS_PORTER_QUEUE
from common.utils import (
    extract_entities_from_checks,
    ip_info_to_ip_schema,
    normilize_ip,
    normilize_server_check,
)

from checker.checks import check_server_by_protocol, check_server_ports
from checker.parsers import parse_masscan_address, parse_porter_address
from checker.services import (
    is_server_in_db,
    save_non_existing_servers,
    save_porter,
)

logger = logging.getLogger(__name__)


async def handle_masscan(address: str) -> None:
    masscan = parse_masscan_address(address)

    # Server check
    check = await check_server_by_protocol(
        masscan.protocol, masscan.ip, masscan.port
    )
    if check is None:
        return

    async with async_session() as db:  # type: ignore
        if await is_server_in_db(db, masscan.ip, masscan.port):
            return

        # Ip
        ip = await get_ip(db, masscan.ip)
        if ip is None:
            ip_info = await get_ip_info(masscan.ip)
            if ip_info is None:
                logger.warning("Unsuccessful ip request")
                ip_info = IpInfoSchema()

            ip_schema = ip_info_to_ip_schema(
                ip_info, masscan.ip, masscan.is_multiport
            )
            normilize_ip(ip_schema)
            ip = create_ip(db, ip_schema)

        # Server
        normilize_server_check(check)
        await upload_servers([check])

        entities = extract_entities_from_checks([check])
        entity_maps = await load_existing_entities(db, entities)

        save_non_existing_servers(db, [check], ip, entity_maps)
        await db.commit()

    logger.info(f"New server: {ip.ip}:{check.server.port}")

    if not ip.is_multiport:
        await ra.rpush(REDIS_PORTER_QUEUE, ip.ip)


async def handle_porter(address: str) -> None:
    ports, ip = parse_porter_address(address)
    defined_ports, checks = await check_server_ports(ports, ip)

    if not defined_ports and not checks:
        return

    async with async_session() as db:  # type: ignore
        ip_model = await get_ip(db, ip)

        # does not happen usually
        if ip_model is None:
            logger.warning(f"{ip} was not found in db")
            return

        for server in checks:
            normilize_server_check(server)
        await upload_servers(checks)
        entities = extract_entities_from_checks(checks)
        entity_maps = await load_existing_entities(db, entities)

        save_porter(db, defined_ports, checks, entity_maps, ip_model)
        await db.commit()

    logger.info(f"Ports and servers of {ip} were saved")
