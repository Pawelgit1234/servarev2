import base64
from datetime import UTC, datetime, timedelta

from common.schemas.assets import ModSchema, PluginSchema, SoftwareSchema
from common.schemas.ip import IpInfoSchema
from common.schemas.server import ServerCheckSchema
from common.settings import (
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
)


def merge_server_check_with_ip_info(
    server: ServerCheckSchema, ip_info: IpInfoSchema
) -> None:
    server.server.country = ip_info.country
    server.server.region = ip_info.region
    server.server.city = ip_info.city
    server.server.latitude = ip_info.latitude
    server.server.longitude = ip_info.longitude
    server.server.hostname = ip_info.hostname
    server.server.asn = ip_info.asn


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


def normilize_server_check(server: ServerCheckSchema) -> None:
    server.server.country = _truncate(
        server.server.country,
        COUNTRY_MAX,
    )  # type: ignore

    server.server.region = _truncate(
        server.server.region,
        REGION_MAX,
    )  # type: ignore

    server.server.city = _truncate(
        server.server.city,
        CITY_MAX,
    )  # type: ignore

    server.server.hostname = _truncate(
        server.server.hostname,
        HOSTNAME_MAX,
    )  # type: ignore

    server.server.asn = _truncate(
        server.server.asn,
        ASN_MAX,
    )  # type: ignore

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
        player_snapshot.name = _truncate(
            player_snapshot.name,
            USERNAME_MAX,
        )  # type: ignore
