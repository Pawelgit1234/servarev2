import logging

from common.models.server import IpModel, ServerModel
from common.schemas.server import ServerCheckSchema
from common.utils import normilize_server_check

logger = logging.getLogger(__name__)


def normilize_server_checks(
    servers: list[tuple[ServerModel, ServerCheckSchema | None]],
) -> list[ServerCheckSchema]:
    active_server_checks = []
    for _, check in servers:
        if check is None:
            continue

        normilize_server_check(check)
        active_server_checks.append(check)

    return active_server_checks


def log_servers_saved(ip: IpModel) -> None:
    log = f"Servers of {ip.ip} were checked: "
    for s in ip.servers:
        log += f"{s.port}, "
    logger.info(log[:-2])  # remove the last comma
