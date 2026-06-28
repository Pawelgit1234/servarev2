import logging

from common.databases import async_session
from common.services.server import upload_servers
from common.utils import normilize_ip_info

from monitor.checks import check_servers
from monitor.services import (
    get_next_server_group,
    prepare_ip_data,
    save_servers,
)
from monitor.utils import log_servers_saved, normilize_server_checks

logger = logging.getLogger(__name__)


async def player_worker() -> None:
    pass


async def server_worker() -> None:
    while True:
        async with async_session() as db:  # type: ignore
            server_models = await get_next_server_group(db)
            servers = await check_servers(server_models)

            # just one of the servers
            server_model = server_models[0] if server_models else None
            if server_model is None:  # happens only if the database is empty
                continue

            ip_info, update_porter = await prepare_ip_data(server_model)
            if ip_info is not None:
                normilize_ip_info(ip_info)

            active_server_checks = normilize_server_checks(servers)
            await upload_servers(active_server_checks)

            await save_servers(db, servers, ip_info, update_porter)
            await db.commit()

        log_servers_saved(server_models)
