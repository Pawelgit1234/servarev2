import logging

from common.models.assets import ModModel, PluginModel, SoftwareModel
from common.models.player import (
    PlayerSnapshotModel,
)
from common.models.server import (
    ServerDynamicSnapshotModel,
    ServerModel,
    ServerSnapshotModel,
)
from common.schemas.assets import ModSchema, PluginSchema, SoftwareSchema
from common.schemas.player import PlayerSnapshotSchema
from common.schemas.server import (
    ServerCheckSchema,
    ServerDynamicSnapshotSchema,
    ServerSnapshotSchema,
)
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


def log_servers_saved(server_models: list[ServerModel]) -> None:
    log = "Servers were checked: "
    for s in server_models:
        log += f" {s.ip}:{s.port},"
    logger.info(log)


def snapshot_changed(
    db_snapshot: ServerSnapshotModel | None,
    new_snapshot: ServerSnapshotSchema,
) -> bool:
    if db_snapshot is None:
        return True

    return (  # type: ignore
        db_snapshot.version != new_snapshot.version
        or db_snapshot.players_max != new_snapshot.players_max
        or db_snapshot.motd != new_snapshot.motd
        or db_snapshot.protocol != new_snapshot.protocol
        or db_snapshot.icon != new_snapshot.icon
        or db_snapshot.enforcesSecureChat != new_snapshot.enforcesSecureChat
        or db_snapshot.fml_network_version != new_snapshot.fml_network_version
        or db_snapshot.mods_truncated != new_snapshot.mods_truncated
        or db_snapshot.map_name != new_snapshot.map_name
        or db_snapshot.gamemode != new_snapshot.gamemode
    )


def dynamic_snapshot_changed(
    db_snapshot: ServerDynamicSnapshotModel | None,
    new_snapshot: ServerDynamicSnapshotSchema,
) -> bool:
    if db_snapshot is None:
        return True

    return db_snapshot.players_online != new_snapshot.players_online  # type: ignore


def software_changed(
    db_software: SoftwareModel | None,
    new_software: SoftwareSchema,
) -> bool:
    if db_software is None:
        return True

    return (  # type: ignore
        db_software.name != new_software.name
        or db_software.version != new_software.version
    )


def plugins_changed(
    db_plugins: list[PluginModel],
    new_plugins: list[PluginSchema],
) -> bool:
    db_set = {(p.name,) for p in db_plugins}
    new_set = {(p.name,) for p in new_plugins}
    return db_set != new_set


def mods_changed(
    db_mods: list[ModModel],
    new_mods: list[ModSchema],
) -> bool:
    db_set = {(m.name, m.version) for m in db_mods}
    new_set = {(m.name, m.version) for m in new_mods}
    return db_set != new_set


def player_snapshot_changed(
    db_snapshot: PlayerSnapshotModel | None,
    new_snapshot: PlayerSnapshotSchema,
) -> bool:
    if db_snapshot is None:
        return True

    return (  # type: ignore
        db_snapshot.name != new_snapshot.name
        or db_snapshot.skin != new_snapshot.skin
        or db_snapshot.cape != new_snapshot.cape
    )


def extract_assets_from_checks(
    servers: list[tuple[ServerModel, ServerCheckSchema | None]],
) -> tuple[list[SoftwareSchema], list[PluginSchema], list[ModSchema]]:
    all_softwares = []
    all_plugins = []
    all_mods = []

    for _, check in servers:
        if not check:
            continue

        all_softwares.append(check.software)
        all_plugins.extend(check.plugins)
        all_mods.extend(check.mods)

    return all_softwares, all_plugins, all_mods


def need_create_server_snapshot(
    server: ServerModel,
    check: ServerCheckSchema,
) -> bool:
    last_snapshot = server.snapshots[0] if server.snapshots else None

    last_software = last_snapshot.software if last_snapshot else None

    last_plugins = (
        [assoc.plugin for assoc in last_snapshot.plugin_associations]
        if last_snapshot
        else []
    )

    last_mods = (
        [assoc.mod for assoc in last_snapshot.mod_associations]
        if last_snapshot
        else []
    )

    return any(
        (
            snapshot_changed(last_snapshot, check.server_snapshot),
            software_changed(last_software, check.software),
            plugins_changed(last_plugins, check.plugins),
            mods_changed(last_mods, check.mods),
        )
    )
