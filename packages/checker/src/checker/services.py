from itertools import product

from common.models.assets import (
    ServerSnapshotModAssociationModel,
    ServerSnapshotPluginAssociationModel,
)
from common.models.player import (
    PlayerModel,
    PlayerSessionModel,
    PlayerSnapshotModel,
)
from common.models.server import (
    ServerDynamicSnapshotModel,
    ServerModel,
    ServerPortAssociationModel,
    ServerPortModel,
    ServerSessionModel,
    ServerSnapshotModel,
)
from common.schemas.server import ServerCheckSchema, ServerPortSchema
from common.services.assets import (
    ensure_mod,
    ensure_plugin,
    ensure_software,
    load_existing_mods,
    load_existing_plugins,
    load_existing_softwares,
)
from common.services.server import ensure_port, load_existing_ports
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from checker.utils import extract_assets_from_checks


async def is_server_in_db(db: AsyncSession, ip: str, port: int) -> bool:
    exists = (
        await db.execute(
            select(ServerModel.id).where(
                ServerModel.ip == ip,
                ServerModel.port == port,
            )
        )
    ).scalar_one_or_none()

    return exists is not None


async def get_servers_with_same_ip(
    db: AsyncSession, ip: str
) -> list[ServerModel]:
    return (
        (await db.execute(select(ServerModel).where(ServerModel.ip == ip)))
        .scalars()
        .all()  # type: ignore
    )


async def load_existing_server_port_associations(
    db: AsyncSession,
    servers: list[ServerModel],
    ports: list[ServerPortModel],
) -> set[tuple[int, int]]:
    server_ids = [s.id for s in servers]
    port_ids = [p.id for p in ports]

    if not server_ids or not port_ids:
        return set()

    rows = (
        await db.execute(
            select(
                ServerPortAssociationModel.server_id,
                ServerPortAssociationModel.server_port_id,
            ).where(
                ServerPortAssociationModel.server_id.in_(server_ids),
                ServerPortAssociationModel.server_port_id.in_(port_ids),
            )
        )
    ).all()

    return set(rows)  # type: ignore


def ensure_server_port_associations(
    db: AsyncSession,
    all_servers: list[ServerModel],
    all_ports: list[ServerPortModel],
    existing_assocs: set[tuple[int, int]],
) -> None:
    for server, port in product(all_servers, all_ports):
        key = (server.id, port.id)

        if key in existing_assocs:
            continue

        db.add(
            ServerPortAssociationModel(
                server=server,
                server_port=port,
            )
        )


async def save_non_existing_servers(
    db: AsyncSession, checks: list[ServerCheckSchema]
) -> list[ServerModel]:
    all_softwares, all_plugins, all_mods = extract_assets_from_checks(checks)
    software_map = await load_existing_softwares(db, all_softwares)
    plugin_map = await load_existing_plugins(db, all_plugins)
    mod_map = await load_existing_mods(db, all_mods)

    server_models = []
    for check in checks:
        # Server
        server = ServerModel(
            ip=check.server.ip,
            port=check.server.port,
            server_type=check.server.server_type,
            is_lan=check.server.is_lan,
            is_multiport=check.server.is_multiport,
            country=check.server.country,
            region=check.server.region,
            city=check.server.city,
            latitude=check.server.latitude,
            longitude=check.server.longitude,
            hostname=check.server.hostname,
            asn=check.server.asn,
        )
        server_models.append(server)
        db.add(server)

        server_snapshot = ServerSnapshotModel(
            server=server,
            version=check.server_snapshot.version,
            players_max=check.server_snapshot.players_max,
            motd=check.server_snapshot.motd,
            latency=check.server_snapshot.latency,
            protocol=check.server_snapshot.protocol,
            icon=check.server_snapshot.icon,
            enforcesSecureChat=check.server_snapshot.enforcesSecureChat,
            fml_network_version=check.server_snapshot.fml_network_version,
            mods_truncated=check.server_snapshot.mods_truncated,
            map_name=check.server_snapshot.map_name,
            gamemode=check.server_snapshot.gamemode,
        )
        db.add(server_snapshot)

        dynamic_snapshot = ServerDynamicSnapshotModel(
            server=server,
            players_online=check.server_dynamic_snapshot.players_online,
        )
        db.add(dynamic_snapshot)

        servers_session = ServerSessionModel(server=server)
        db.add(servers_session)

        # Player
        for player_schema, snapshot_schema in check.players.items():
            player = PlayerModel(
                player_type=player_schema.player_type,
                uuid=player_schema.uuid,
            )
            db.add(player)

            player_snapshot = PlayerSnapshotModel(
                player=player,
                name=snapshot_schema.name,
                skin=snapshot_schema.skin,
                cape=snapshot_schema.cape,
            )
            db.add(player_snapshot)

            player_session = PlayerSessionModel(server=server, player=player)
            db.add(player_session)

        # Assets
        software = ensure_software(db, software_map, check.software)
        server_snapshot.software = software

        for p in check.plugins:
            plugin = ensure_plugin(db, plugin_map, p)
            server_snapshot.plugin_associations.append(
                ServerSnapshotPluginAssociationModel(plugin=plugin)
            )

        for m in check.mods:
            mod = ensure_mod(db, mod_map, m)
            server_snapshot.mod_associations.append(
                ServerSnapshotModAssociationModel(mod=mod)
            )

    return server_models


async def save_ports(
    db: AsyncSession,
    ports: list[ServerPortSchema],
    servers: list[ServerCheckSchema],
    ip: str,
) -> None:
    # servers
    existing_servers = await get_servers_with_same_ip(db, ip)
    existing_servers_map = {(s.ip, s.port): s for s in existing_servers}

    all_servers: list[ServerModel] = []
    new_servers: list[ServerCheckSchema] = []

    for server_data in servers:
        server_key = (server_data.server.ip, server_data.server.port)
        server = existing_servers_map.get(server_key)

        if server is None:
            new_servers.append(server_data)
        else:
            all_servers.append(server)

    all_servers.extend(await save_non_existing_servers(db, new_servers))

    # Ports
    port_map = await load_existing_ports(db, ports)
    all_ports: list[ServerPortModel] = []
    for port_schema in ports:
        all_ports.append(ensure_port(db, port_map, port_schema))

    await db.flush()

    # Associations
    existing_assocs = await load_existing_server_port_associations(
        db, all_servers, all_ports
    )
    ensure_server_port_associations(
        db, all_servers, all_ports, existing_assocs
    )
