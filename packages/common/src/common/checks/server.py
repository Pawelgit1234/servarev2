import logging
import re

from common.checks.player import fetch_players
from common.enums import ServerSoftwareType, ServerType
from common.schemas.assets import ModSchema, PluginSchema, SoftwareSchema
from common.schemas.server import (
    ServerCheckSchema,
    ServerDynamicSnapshotSchema,
    ServerSchema,
    ServerSnapshotSchema,
)
from common.settings import SERVER_CHECK_TIMEOUT
from mcstatus import BedrockServer, JavaServer, LegacyServer
from mcstatus.responses import JavaStatusResponse

logger = logging.getLogger(__name__)

for name in (
    "asyncio",
    "mcstatus",
    "dns",
    "aiosqlite",
):
    logging.getLogger(name).setLevel(logging.CRITICAL)

DETECTION_ORDER: tuple[ServerSoftwareType, ...] = (
    ServerSoftwareType.FABRIC,
    ServerSoftwareType.QUILT,
    ServerSoftwareType.NEOFORGE,
    ServerSoftwareType.VELOCITY,
    ServerSoftwareType.WATERFALL,
    ServerSoftwareType.BUNGEE,
    ServerSoftwareType.PAPER,
    ServerSoftwareType.PURPUR,
    ServerSoftwareType.PUFFERFISH,
    ServerSoftwareType.TUINITY,
    ServerSoftwareType.AIRPLANE,
    ServerSoftwareType.SPIGOT,
    ServerSoftwareType.CRAFTBUKKIT,
    ServerSoftwareType.BUKKIT,
    ServerSoftwareType.SPONGE,
    ServerSoftwareType.SPONGEFORGE,
    ServerSoftwareType.SPONGEVANILLA,
    ServerSoftwareType.ARCLIGHT,
    ServerSoftwareType.MOHIST,
    ServerSoftwareType.MAGMA,
    ServerSoftwareType.CATSERVER,
)


def detect_server_software(data: str) -> ServerSoftwareType:
    for software in DETECTION_ORDER:
        if software.value in data:
            return software

    return ServerSoftwareType.VANILLA


def detect_server_software_by_status(
    status: JavaStatusResponse,
) -> ServerSoftwareType:
    raw = status.raw
    name = status.version.name.lower()
    motd = status.description.lower()

    full = f"{name} {motd}"

    if "modinfo" in raw:
        return ServerSoftwareType.FORGE

    return detect_server_software(full)


def is_lan(players_online: int, players_max: int, motd: str) -> bool:
    pattern = r"^[A-Za-z0-9_ ]+\s*-\s*.+$"
    valid_lan_motd = bool(re.match(pattern, motd))

    return (
        " - " in motd
        and players_online >= 1
        and players_max == 8
        and valid_lan_motd
    )


async def check_java_server(ip: str, port: int) -> ServerCheckSchema | None:
    try:
        server = await JavaServer.async_lookup(
            f"{ip}:{port}",
            SERVER_CHECK_TIMEOUT,  # type: ignore
        )
        status = await server.async_status()
    except Exception:
        return None

    try:
        query = await server.async_query()
    except Exception:
        query = None

    # --- players ---
    players = (
        await fetch_players(status.players.sample)
        if status.players.sample
        else {}
    )

    # --- forge ---
    forge = status.forge_data
    fml = forge.fml_network_version if forge else None
    truncated = forge.truncated if forge else None

    mods = (
        [ModSchema(name=m.name, version=m.marker) for m in forge.mods]
        if forge
        else []
    )

    # --- query ---
    if query:
        plugins = [PluginSchema(name=name) for name in query.software.plugins]
        software = SoftwareSchema(
            name=detect_server_software(query.software.brand),
            version=query.software.version,
        )
        map_name = query.map_name
    else:
        plugins = []
        software = SoftwareSchema(
            name=detect_server_software_by_status(status),
            version=status.version.name,
        )
        map_name = None

    # --- schemas ---
    return ServerCheckSchema(
        server=ServerSchema(
            ip=ip,
            port=port,
            server_type=ServerType.JAVA,
            is_lan=is_lan(
                status.players.online,
                status.players.max,
                status.motd.to_plain(),
            ),
        ),
        server_snapshot=ServerSnapshotSchema(
            version=status.version.name,
            players_max=status.players.max,
            motd=status.description,
            latency=status.latency,
            protocol=status.version.protocol,
            icon=status.icon,
            enforcesSecureChat=status.enforces_secure_chat,
            fml_network_version=fml,
            mods_truncated=truncated,
            map_name=map_name,
        ),
        server_dynamic_snapshot=ServerDynamicSnapshotSchema(
            players_online=status.players.online
        ),
        players=players,
        software=software,
        mods=mods,
        plugins=plugins,
    )


async def check_bedrock_server(ip: str, port: int) -> ServerCheckSchema | None:
    try:
        server = BedrockServer.lookup(f"{ip}:{port}", SERVER_CHECK_TIMEOUT)  # type: ignore
        status = await server.async_status()
    except Exception:
        return None

    return ServerCheckSchema(
        server=ServerSchema(
            ip=ip,
            port=port,
            server_type=ServerType.BEDROCK,
            is_lan=False,
        ),
        server_snapshot=ServerSnapshotSchema(
            version=status.version.name,
            players_max=status.players.max,
            motd=status.description,
            latency=status.latency,
            map_name=status.map_name,
            gamemode=status.gamemode,
        ),
        server_dynamic_snapshot=ServerDynamicSnapshotSchema(
            players_online=status.players.online
        ),
        players={},
        software=SoftwareSchema(
            name=ServerSoftwareType.VANILLA,
            version=status.version.name,
        ),
        mods=[],
        plugins=[],
    )


async def check_legacy_server(ip: str, port: int) -> ServerCheckSchema | None:
    try:
        server = await LegacyServer.async_lookup(
            f"{ip}:{port}",
            SERVER_CHECK_TIMEOUT,  # type: ignore
        )
        status = await server.async_status()
    except Exception:
        return None

    return ServerCheckSchema(
        server=ServerSchema(
            ip=ip,
            port=port,
            server_type=ServerType.LEGACY,
            is_lan=is_lan(
                status.players.online,
                status.players.max,
                status.motd.to_plain(),
            ),
        ),
        server_snapshot=ServerSnapshotSchema(
            version=status.version.name,
            players_max=status.players.max,
            motd=status.description,
            latency=status.latency,
            protocol=status.version.protocol,
        ),
        server_dynamic_snapshot=ServerDynamicSnapshotSchema(
            players_online=status.players.online if status.players else 0
        ),
        players={},
        software=SoftwareSchema(
            name=ServerSoftwareType.VANILLA,
            version=status.version.name,
        ),
        mods=[],
        plugins=[],
    )


CHECKERS = {
    ServerType.JAVA: check_java_server,
    ServerType.BEDROCK: check_bedrock_server,
    ServerType.LEGACY: check_legacy_server,
}


async def check_server_by_type(
    ip: str, port: int, server_type: ServerType
) -> ServerCheckSchema | None:
    checker = CHECKERS[server_type]
    return await checker(ip, port)
