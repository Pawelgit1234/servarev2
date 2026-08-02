from common.enums import DetectedServiceType, ProtocolType
from common.models.assets import (
    ServerSnapshotModAssociationModel,
    ServerSnapshotPluginAssociationModel,
)
from common.models.server import (
    IpModel,
    IpPortModel,
    ServerDynamicSnapshotModel,
    ServerModel,
    ServerSessionModel,
    ServerSnapshotModel,
)
from common.schemas.common import ExistingEntityMapsSchema
from common.schemas.server import IpPortSchema, ServerCheckSchema
from common.services.assets import (
    ensure_mod,
    ensure_plugin,
    ensure_software,
)
from common.services.server import handle_player_join, save_servers
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def is_server_in_db(db: AsyncSession, ip: str, port: int) -> bool:
    exists = (
        await db.execute(
            select(ServerModel.id)
            .join(ServerModel.ip)
            .where(
                IpModel.ip == ip,
                ServerModel.port == port,
            )
        )
    ).scalar_one_or_none()

    return exists is not None


def ensure_ip_port(
    db: AsyncSession,
    ip: IpModel,
    port_map: dict[tuple[int, ProtocolType, DetectedServiceType], IpPortModel],
    port_schema: IpPortSchema,
) -> IpPortModel:
    key = (
        port_schema.port,
        port_schema.protocol_type,
        port_schema.detected_service_type,
    )

    port = port_map.get(key)
    if port is None:
        port = IpPortModel(
            ip=ip,
            port=port_schema.port,
            protocol_type=port_schema.protocol_type,
            detected_service_type=port_schema.detected_service_type,
        )

        db.add(port)
        port_map[key] = port

    return port


def save_non_existing_servers(
    db: AsyncSession,
    checks: list[ServerCheckSchema],
    ip: IpModel,
    em: ExistingEntityMapsSchema,
) -> list[ServerModel]:
    server_models = []
    for check in checks:
        # Server
        server = ServerModel(
            ip=ip,
            port=check.server.port,
            server_type=check.server.server_type,
            is_lan=check.server.is_lan,
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

        # Players
        for player_schema, snapshot_schema in check.players.items():
            handle_player_join(
                db, em.player_map, server, player_schema, snapshot_schema
            )

        # Assets
        software = ensure_software(db, em.software_map, check.software)
        server_snapshot.software = software

        for p in check.plugins:
            plugin = ensure_plugin(db, em.plugin_map, p)
            server_snapshot.plugin_associations.append(
                ServerSnapshotPluginAssociationModel(plugin=plugin)
            )

        for m in check.mods:
            mod = ensure_mod(db, em.mod_map, m)
            server_snapshot.mod_associations.append(
                ServerSnapshotModAssociationModel(mod=mod)
            )

    return server_models


def save_porter(
    db: AsyncSession,
    ports: list[IpPortSchema],
    checks: list[ServerCheckSchema],
    entity_maps: ExistingEntityMapsSchema,
    ip: IpModel,
) -> None:
    # servers
    existing_servers_map = {s.port: s for s in ip.servers}

    new_servers: list[ServerCheckSchema] = []
    old_servers: list[tuple[ServerModel, ServerCheckSchema]] = []

    for check in checks:
        server = existing_servers_map.get(check.server.port)
        if server is None:
            new_servers.append(check)
        else:
            old_servers.append((server, check))

    save_non_existing_servers(db, new_servers, ip, entity_maps)
    save_servers(db, old_servers, entity_maps)  # type: ignore

    # ports
    port_map = {
        (p.port, p.protocol_type, p.detected_service_type): p for p in ip.ports
    }

    for port_schema in ports:
        ensure_ip_port(db, ip, port_map, port_schema)
