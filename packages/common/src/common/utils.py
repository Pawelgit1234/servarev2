import asyncio
import base64
import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from functools import wraps
from random import uniform
from typing import Any, ParamSpec, TypeVar

from common.models.assets import ModModel, PluginModel, SoftwareModel
from common.models.player import PlayerSnapshotModel
from common.models.server import (
    ServerDynamicSnapshotModel,
    ServerModel,
    ServerSnapshotModel,
)
from common.schemas.assets import ModSchema, PluginSchema, SoftwareSchema
from common.schemas.common import ExtractedEntitiesSchema
from common.schemas.ip import IpInfoSchema
from common.schemas.player import PlayerSchema, PlayerSnapshotSchema
from common.schemas.server import (
    IpSchema,
    ServerCheckSchema,
    ServerDynamicSnapshotSchema,
    ServerSnapshotSchema,
)
from common.settings import (
    API_BASE_DELAY_SECONDS,
    API_MAX_ATTEMPTS,
    API_MAX_DELAY_SECONDS,
    ASN_MAX,
    CITY_MAX,
    COUNTRY_MAX,
    HOSTNAME_MAX,
    MOD_NAME_MAX,
    MOD_VERSION_MAX,
    PLUGIN_NAME_MAX,
    REGION_MAX,
    SERVER_GAMEMODE_MAX,
    SERVER_MAP_NAME_MAX,
    SERVER_MOTD_MAX,
    SERVER_VERSION_MAX,
    SOFTWARE_VERSION_MAX,
    USERNAME_MAX,
    WORKER_RESTART_ON_FAILURE_DELAY,
)

logger = logging.getLogger(__name__)

# def merge_server_check_with_ip_info(
#     server: ServerCheckSchema, ip_info: IpInfoSchema
# ) -> None:
#     server.server.country = ip_info.country
#     server.server.region = ip_info.region
#     server.server.city = ip_info.city
#     server.server.latitude = ip_info.latitude
#     server.server.longitude = ip_info.longitude
#     server.server.hostname = ip_info.hostname
#     server.server.asn = ip_info.asn


def ip_info_to_ip_schema(
    ip_info: IpInfoSchema, ip: str, is_multiport: bool
) -> IpSchema:
    return IpSchema(
        country=ip_info.country,
        region=ip_info.region,
        city=ip_info.city,
        latitude=ip_info.latitude,
        longitude=ip_info.longitude,
        hostname=ip_info.hostname,
        asn=ip_info.asn,
        ip=ip,
        is_multiport=is_multiport,
    )


def decode_base64(string: str) -> bytes | None:
    try:
        if "," in string:
            string = string.split(",", 1)[1]

        return base64.b64decode(string)
    except Exception:
        return None


def has_expired(timestamp: datetime, delta: int) -> bool:
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)

    return datetime.now(UTC) > (  # type: ignore
        timestamp + timedelta(days=delta)
    )


def _truncate(value: str | None, limit: int) -> str | None:
    if value is None:
        return None

    return value.strip()[:limit]


def normilize_ip(ip: IpInfoSchema | IpSchema) -> None:
    ip.country = _truncate(
        ip.country,
        COUNTRY_MAX,
    )  # type: ignore

    ip.region = _truncate(
        ip.region,
        REGION_MAX,
    )  # type: ignore

    ip.city = _truncate(
        ip.city,
        CITY_MAX,
    )  # type: ignore

    ip.hostname = _truncate(
        ip.hostname,
        HOSTNAME_MAX,
    )  # type: ignore

    ip.asn = _truncate(
        ip.asn,
        ASN_MAX,
    )  # type: ignore


def normalize_player_snapshot(
    player_snapshot: PlayerSnapshotSchema | PlayerSnapshotModel,
) -> None:
    player_snapshot.name = _truncate(
        player_snapshot.name,
        USERNAME_MAX,
    )  # type: ignore


def normilize_server_check(server: ServerCheckSchema) -> None:
    # Snapshot
    server.server_snapshot.version = _truncate(
        server.server_snapshot.version,
        SERVER_VERSION_MAX,
    )  # type: ignore

    server.server_snapshot.motd = _truncate(
        server.server_snapshot.motd,
        SERVER_MOTD_MAX,
    )  # type: ignore

    server.server_snapshot.map_name = _truncate(
        server.server_snapshot.map_name,
        SERVER_MAP_NAME_MAX,
    )  # type: ignore

    server.server_snapshot.gamemode = _truncate(
        server.server_snapshot.gamemode,
        SERVER_GAMEMODE_MAX,
    )  # type: ignore

    # Software
    server.software = SoftwareSchema(
        name=server.software.name,
        version=_truncate(server.software.version, SOFTWARE_VERSION_MAX),  # type: ignore
    )

    # Mods
    server.mods = [
        ModSchema(
            name=_truncate(m.name, MOD_NAME_MAX),  # type: ignore
            version=_truncate(m.version, MOD_VERSION_MAX),  # type: ignore
        )
        for m in server.mods
    ]

    # Plugins
    server.plugins = [
        PluginSchema(
            name=_truncate(p.name, PLUGIN_NAME_MAX)  # type: ignore
        )
        for p in server.plugins
    ]

    # Players
    for player_snapshot in server.players.values():
        normalize_player_snapshot(player_snapshot)


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


def extract_entities_from_checks(
    checks: list[ServerCheckSchema],
) -> ExtractedEntitiesSchema:
    softwares: list[SoftwareSchema] = []
    plugins: list[PluginSchema] = []
    mods: list[ModSchema] = []
    players: list[PlayerSchema] = []

    for check in checks:
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


P = ParamSpec("P")
T = TypeVar("T")


def retry_on_none(
    max_attempts: int = API_MAX_ATTEMPTS,  # type: ignore
    base_delay_seconds: int = API_BASE_DELAY_SECONDS,  # type: ignore
    max_delay_seconds: int = API_MAX_DELAY_SECONDS,  # type: ignore
) -> Callable[
    [Callable[P, Awaitable[T | None]]], Callable[P, Awaitable[T | None]]
]:
    def decorator(
        func: Callable[P, Awaitable[T | None]],
    ) -> Callable[P, Awaitable[T | None]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T | None:
            for attempt in range(max_attempts):
                result = await func(*args, **kwargs)

                if result is not None:
                    return result

                delay_seconds = uniform(
                    0, min(max_delay_seconds, base_delay_seconds * 2**attempt)
                )

                await asyncio.sleep(delay_seconds)

            return None

        return wrapper

    return decorator


def restart_on_failure(
    name: str | Callable[..., str],
    delay: float = WORKER_RESTART_ON_FAILURE_DELAY,  # type: ignore
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[None]]]:
    def decorator(
        func: Callable[..., Awaitable[T]],
    ) -> Callable[..., Awaitable[None]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> None:
            worker_name = name(*args, **kwargs) if callable(name) else name
            while True:
                try:
                    logger.info("Starting worker %s", worker_name)
                    await func(*args, **kwargs)
                except asyncio.CancelledError:
                    logger.info("Worker %s cancelled", worker_name)
                    raise
                except Exception:
                    logger.exception(
                        "Worker %s crashed, restarting", worker_name
                    )
                    await asyncio.sleep(delay)

        return wrapper

    return decorator
