import logging

from common.models.server import IpModel, ServerModel
from common.schemas.assets import ModSchema, PluginSchema, SoftwareSchema
from common.schemas.common import ExtractedEntitiesSchema
from common.schemas.player import PlayerSchema
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
    logger.info(log)


def extract_assets_from_servers(
    servers: list[tuple[ServerModel, ServerCheckSchema | None]],
) -> ExtractedEntitiesSchema:
    softwares: list[SoftwareSchema] = []
    plugins: list[PluginSchema] = []
    mods: list[ModSchema] = []
    players: list[PlayerSchema] = []

    for _, check in servers:
        if not check:
            continue

        softwares.append(check.software)
        plugins.extend(check.plugins)
        mods.extend(check.mods)
        players.extend(check.players.keys())

    return ExtractedEntitiesSchema(
        softwares=softwares,
        plugins=plugins,
        mods=mods,
        players=players,
    )
