import logging

from common.databases import async_session
from common.services.common import load_existing_entities, upload_servers
from common.services.server import save_servers
from common.utils import normilize_ip

from monitor.checks import check_servers
from monitor.services import get_next_server_group, prepare_ip_data
from monitor.utils import (
    extract_assets_from_servers,
    log_servers_saved,
    normilize_server_checks,
)

logger = logging.getLogger(__name__)


async def player_worker() -> None:
    pass


# TODO: просто продолжай решать ошибки
async def server_worker() -> None:
    while True:
        async with async_session() as db:  # type: ignore
            server_models = await get_next_server_group(db)
            servers = await check_servers(server_models)

            # just one of the servers
            server_model = server_models[0] if server_models else None
            if server_model is None:  # happens only if the database is empty
                logger.warning("Database ist empty")
                continue

            # TODO: use IpSchema instead of IpInfoSchema ???
            ip_info, update_porter = await prepare_ip_data(server_model)
            if ip_info is not None:
                normilize_ip(ip_info)

            active_server_checks = normilize_server_checks(servers)
            await upload_servers(active_server_checks)

            entities = extract_assets_from_servers(servers)
            entity_maps = await load_existing_entities(db, entities)
            save_servers(db, servers, ip_info, update_porter, entity_maps)
            await db.commit()

        log_servers_saved(server_models)
