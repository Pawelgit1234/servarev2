import logging

from common.checks.ip import get_ip_info
from common.databases import async_session, ra
from common.logger import setup_logging
from common.services.server import upload_servers
from common.settings import (
    IP_CHECK_INTERVAL_DAYS,
    PORTER_CHECK_INTERVAL_DAYS,
    REDIS_PORTER_QUEUE,
)
from common.utils import has_expired

from monitor.checks import check_servers
from monitor.services import get_next_server_group, save_servers
from monitor.utils import normilize_server_checks

setup_logging()
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

            active_server_checks = normilize_server_checks(servers)
            await upload_servers(active_server_checks)

            # TODO: break in functions

            ip_info = None
            porter_date = False

            if has_expired(
                server_model.last_ip_check_at,
                IP_CHECK_INTERVAL_DAYS,  # type: ignore
            ):
                ip_info = await get_ip_info(server_model.ip)

            if (
                has_expired(
                    server_model.last_porter_check_at,
                    PORTER_CHECK_INTERVAL_DAYS,  # type: ignore
                )
                and not server_model.is_multiport
            ):
                await ra.rpush(REDIS_PORTER_QUEUE, server_model.ip)  # type: ignore
                porter_date = True

            await save_servers(db, servers, ip_info, porter_date)
            await db.commit()

            log = "Servers were checked: "
            for s in server_models:
                log += f" {s.ip}:{s.port},"
            logger.info(log)
