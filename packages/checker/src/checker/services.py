from common.models.assets import (
    ModModel,
    PluginModel,
    ServerSnapshotModAssociationModel,
    ServerSnapshotPluginAssociationModel,
    SoftwareModel,
)
from common.models.player import (
    PlayerModel,
    PlayerSessionModel,
    PlayerSnapshotModel,
    ServerPlayerAssociationModel,
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
from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession


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


async def save_non_existing_server(
    db: AsyncSession, data: ServerCheckSchema
) -> None:
    # Server
    server = ServerModel(
        ip=data.server.ip,
        port=data.server.port,
        server_type=data.server.server_type,
        is_lan=data.server.is_lan,
        is_multiport=data.server.is_multiport,
        country=data.server.country,
        region=data.server.region,
        city=data.server.city,
        latitude=data.server.latitude,
        longitude=data.server.longitude,
        hostname=data.server.hostname,
        asn=data.server.asn,
    )
    db.add(server)

    server_snapshot = ServerSnapshotModel(
        server=server,
        version=data.server_snapshot.version,
        players_max=data.server_snapshot.players_max,
        motd=data.server_snapshot.motd,
        latency=data.server_snapshot.latency,
        protocol=data.server_snapshot.protocol,
        icon=data.server_snapshot.icon,
        enforcesSecureChat=data.server_snapshot.enforcesSecureChat,
        fml_network_version=data.server_snapshot.fml_network_version,
        mods_truncated=data.server_snapshot.mods_truncated,
        map_name=data.server_snapshot.map_name,
        gamemode=data.server_snapshot.gamemode,
    )
    db.add(server_snapshot)

    dynamic_snapshot = ServerDynamicSnapshotModel(
        server=server,
        players_online=data.server_dynamic_snapshot.players_online,
    )
    db.add(dynamic_snapshot)

    servers_session = ServerSessionModel(server=server)
    db.add(servers_session)

    # Player
    for player_schema, snapshot_schema in data.players.items():
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

        association = ServerPlayerAssociationModel(
            server=server,
            player=player,
        )
        db.add(association)

        player_session = PlayerSessionModel(player=player)
        db.add(player_session)

    # Assets
    software = (
        await db.execute(
            select(SoftwareModel).where(
                SoftwareModel.name == data.software.name,
                SoftwareModel.version == data.software.version,
            )
        )
    ).scalar_one_or_none()

    if software is None:
        software = SoftwareModel(
            name=data.software.name,
            version=data.software.version,
        )
        db.add(software)
    server_snapshot.software = software

    mods_keys = {(m.name, m.version) for m in data.mods}
    mods_rows = (
        (
            await db.execute(
                select(ModModel).where(
                    tuple_(ModModel.name, ModModel.version).in_(mods_keys)
                )
            )
        )
        .scalars()
        .all()
    )
    mods_map = {(m.name, m.version): m for m in mods_rows}

    for m in data.mods:
        key = (m.name, m.version)

        mod = mods_map.get(key)
        if mod is None:
            mod = ModModel(name=m.name, version=m.version)
            db.add(mod)

        server_snapshot.mod_associations.append(
            ServerSnapshotModAssociationModel(mod=mod)
        )

    plugin_names = {p.name for p in data.plugins}
    plugins_rows = (
        (
            await db.execute(
                select(PluginModel).where(PluginModel.name.in_(plugin_names))
            )
        )
        .scalars()
        .all()
    )
    plugins_map = {p.name: p for p in plugins_rows}

    for p in data.plugins:
        plugin = plugins_map.get(p.name)

        if plugin is None:
            plugin = PluginModel(name=p.name)
            db.add(plugin)

        server_snapshot.plugin_associations.append(
            ServerSnapshotPluginAssociationModel(plugin=plugin)
        )


async def save_ports(
    db: AsyncSession,
    ports: list[ServerPortSchema],
    servers: list[ServerCheckSchema],
    ip: str,
) -> None:
    if not servers and not ports:
        return

    # servers
    existing_servers = (
        (await db.execute(select(ServerModel).where(ServerModel.ip == ip)))
        .scalars()
        .all()
    )

    existing_servers_map = {(s.ip, s.port): s for s in existing_servers}

    all_servers: list[ServerModel] = []

    for server_data in servers:
        server_key = (server_data.server.ip, server_data.server.port)

        server = existing_servers_map.get(server_key)

        if server is None:
            server = ServerModel(
                ip=server_data.server.ip,
                port=server_data.server.port,
                server_type=server_data.server.server_type,
                is_lan=server_data.server.is_lan,
                is_multiport=server_data.server.is_multiport,
                country=server_data.server.country,
                region=server_data.server.region,
                city=server_data.server.city,
                latitude=server_data.server.latitude,
                longitude=server_data.server.longitude,
                hostname=server_data.server.hostname,
                asn=server_data.server.asn,
            )

            db.add(server)

        all_servers.append(server)

    # Ports
    port_keys = {
        (p.port, p.protocol_type, p.detected_service_type) for p in ports
    }

    existing_ports = (
        (
            await db.execute(
                select(ServerPortModel).where(
                    tuple_(
                        ServerPortModel.port,
                        ServerPortModel.protocol_type,
                        ServerPortModel.detected_service_type,
                    ).in_(port_keys)
                )
            )
        )
        .scalars()
        .all()
    )

    port_map = {
        (p.port, p.protocol_type, p.detected_service_type): p
        for p in existing_ports
    }

    all_ports: list[ServerPortModel] = []

    for p in ports:
        port_key = (p.port, p.protocol_type, p.detected_service_type)
        port = port_map.get(port_key)

        if port is None:
            port = ServerPortModel(
                port=p.port,
                protocol_type=p.protocol_type,
                detected_service_type=p.detected_service_type,
            )
            db.add(port)

        all_ports.append(port)

    await db.flush()

    # Associations
    existing_assocs = set(
        (
            await db.execute(
                select(
                    ServerPortAssociationModel.server_id,
                    ServerPortAssociationModel.server_port_id,
                ).where(
                    ServerPortAssociationModel.server_id.in_(
                        [s.id for s in all_servers]
                    ),
                    ServerPortAssociationModel.server_port_id.in_(
                        [p.id for p in all_ports]
                    ),
                )
            )
        ).all()
    )

    for server in all_servers:
        for port in all_ports:
            key = (server.id, port.id)

            if key in existing_assocs:
                continue

            db.add(
                ServerPortAssociationModel(
                    server=server,
                    server_port=port,
                )
            )
