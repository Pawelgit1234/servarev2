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
from common.utils import (
    has_expired,
    merge_server_check_with_ip_info,
    normilize_server_check,
)

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
            servers = await check_servers(server_models)
            s = server_models[0]

            need_ip_info = has_expired(
                s.last_ip_check_at,
                IP_CHECK_INTERVAL_DAYS,  # type: ignore
            )

            # TODO: break in functions

            ip_info = IpInfoSchema()
            update_ip_timestamp = False
            update_porter_timestamp = False

            if need_ip_info:
                ip_info = await get_ip_info(s.ip)
                update_ip_timestamp = True

            server_checks: list[ServerCheckSchema] = []
            for _, check in servers:
                merge_server_check_with_ip_info(check, ip_info)
                normilize_server_check(check)
                server_checks.append(check)

            await upload_servers(server_checks)

            if (
                has_expired(s.last_porter_check_at, PORTER_CHECK_INTERVAL_DAYS)  # type: ignore
                and not s.is_multiport
            ):
                await ra.rpush(REDIS_PORTER_QUEUE, s.ip)  # type: ignore
                update_porter_timestamp = True

            await save_servers(
                db, servers, update_ip_timestamp, update_porter_timestamp
            )
            await db.commit()
