import logging

from common.checks.ip import get_ip_info
from common.databases import async_session, ra
from common.logger import setup_logging
from common.schemas.ip import IpInfoSchema
from common.schemas.server import ServerCheckSchema
from common.services.server import upload_servers
from common.settings import (
    IP_CHECK_INTERVAL_DAYS,
    PORTER_CHECK_INTERVAL_DAYS,
    REDIS_PORTER_QUEUE,
)
from common.utils import has_expired, normilize_server_check

from monitor.checks import check_servers
from monitor.services import get_next_server_group, save_servers

setup_logging()
logger = logging.getLogger(__name__)


async def player_worker() -> None:
    pass


async def server_worker() -> None:
    while True:
        async with async_session() as db:  # type: ignore
            server_models = await get_next_server_group(db)
            server_checks = await check_servers(server_models)

            # just one of the servers
            server = server_models[0] if server_models else None
            if server is None:
                continue

            need_ip_info = has_expired(
                server.last_ip_check_at,
                IP_CHECK_INTERVAL_DAYS,  # type: ignore
            )

            # TODO: break in functions

            ip_info = IpInfoSchema()
            update_ip = False
            update_porter = False

            if need_ip_info:
                ip_info = await get_ip_info(server.ip)
                update_ip = True

            active_server_checks: list[ServerCheckSchema] = []
            for _, check in server_checks:
                if check is None:
                    continue

                normilize_server_check(check)
                active_server_checks.append(check)

            await upload_servers(active_server_checks)

            if (
                has_expired(
                    server.last_porter_check_at,
                    PORTER_CHECK_INTERVAL_DAYS,  # type: ignore
                )
                and not server.is_multiport
            ):
                await ra.rpush(REDIS_PORTER_QUEUE, server.ip)  # type: ignore
                update_porter = True

            await save_servers(
                db, server_checks, ip_info, update_ip, update_porter
            )
            await db.commit()

            log = "Servers were checked: "
            for s in server_models:
                log += f" {s.ip}:{s.port},"
            logger.info(log)
