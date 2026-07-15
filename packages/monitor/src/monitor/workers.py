import logging

from common.databases import async_session
from common.services.common import load_existing_entities, upload_servers
from common.services.server import save_servers, update_ip_state
from common.utils import normilize_ip

from monitor.checks import check_servers
from monitor.services import get_next_ip, prepare_ip_data
from monitor.utils import (
    extract_assets_from_servers,
    log_servers_saved,
    normilize_server_checks,
)

logger = logging.getLogger(__name__)


async def player_worker() -> None:
    pass


async def server_worker() -> None:
    while True:
        async with async_session() as db:  # type: ignore
            # get ip
            ip = await get_next_ip(db)
            if ip is None:  # happens only if the database is empty
                logger.warning("Database ist empty")
                continue

            # ip
            ip_info, update_porter = await prepare_ip_data(ip)
            if ip_info is not None:
                normilize_ip(ip_info)
            update_ip_state(ip, ip_info, update_porter)

            # server
            servers = await check_servers(ip.ip, ip.servers)
            active_server_checks = normilize_server_checks(servers)
            await upload_servers(active_server_checks)

            entities = extract_assets_from_servers(servers)
            entity_maps = await load_existing_entities(db, entities)
            save_servers(db, servers, entity_maps)

            await db.commit()

        log_servers_saved(ip)
