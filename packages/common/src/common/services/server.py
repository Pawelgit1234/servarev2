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
)
from common.models.server import (
    IpModel,
    ServerDynamicSnapshotModel,
    ServerModel,
    ServerSessionModel,
    ServerSnapshotModel,
)
from common.schemas.assets import ModSchema, PluginSchema, SoftwareSchema
from common.schemas.common import ExistingEntityMapsSchema
from common.schemas.ip import IpInfoSchema
from common.schemas.player import PlayerSchema, PlayerSnapshotSchema
from common.schemas.server import IpSchema, ServerCheckSchema
from common.services.assets import ensure_mod, ensure_plugin, ensure_software
from common.utils import (
    dynamic_snapshot_changed,
    need_create_server_snapshot,
    player_snapshot_changed,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


async def get_ip(db: AsyncSession, ip: str) -> IpModel | None:
    return await db.scalar(  # type: ignore
        select(IpModel)
        .where(IpModel.ip == ip)
        .options(selectinload(IpModel.servers), selectinload(IpModel.ports))
    )


def create_ip(db: AsyncSession, ip: IpSchema) -> IpModel:
    ip_model = IpModel(
        ip=ip.ip,
        is_multiport=ip.is_multiport,
        country=ip.country,
        region=ip.region,
        city=ip.city,
        latitude=ip.latitude,
        longitude=ip.longitude,
        hostname=ip.hostname,
        asn=ip.asn,
    )
    db.add(ip_model)
    return ip_model


def update_ip_state(
    ip: IpModel, ip_info: IpInfoSchema | None, update_porter: bool
) -> None:
    if ip_info is not None and ip_info.country is not None:
        ip.last_ip_check_at = func.now()

        ip.country = ip_info.country
        ip.region = ip_info.region
        ip.city = ip_info.city
        ip.latitude = ip_info.latitude
        ip.longitude = ip_info.longitude
        ip.hostname = ip_info.hostname
        ip.asn = ip_info.asn

    if update_porter:
        ip.last_porter_check_at = func.now()


def handle_server_session(
    db: AsyncSession, server: ServerModel, check: ServerCheckSchema | None
) -> ServerSessionModel | None:
    last_session = server.sessions[0] if server.sessions else None

    # server inactive
    if check is None:
        if last_session is not None and last_session.to is None:
            last_session.to = func.now()

        return None

    # server active
    if last_session is None or last_session.to is not None:
        new_session = ServerSessionModel(server=server)
        db.add(new_session)
        return new_session

    return last_session


def handle_server_snapshot(
    db: AsyncSession,
    server: ServerModel,
    check: ServerCheckSchema,
    software_map: dict[SoftwareSchema, SoftwareModel],
    plugin_map: dict[PluginSchema, PluginModel],
    mod_map: dict[ModSchema, ModModel],
) -> None:
    if need_create_server_snapshot(server, check):
        new_snapshot = ServerSnapshotModel(
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
        db.add(new_snapshot)

        # == Software ==
        software = ensure_software(db, software_map, check.software)
        new_snapshot.software = software  # type: ignore

        # == Plugins ==
        for p in check.plugins:
            plugin = ensure_plugin(db, plugin_map, p)
            new_snapshot.plugin_associations.append(
                ServerSnapshotPluginAssociationModel(plugin=plugin)
            )

        # == Mods ==
        for m in check.mods:
            mod = ensure_mod(db, mod_map, m)
            new_snapshot.mod_associations.append(
                ServerSnapshotModAssociationModel(mod=mod)
            )


def handle_dynamic_snapshot(
    db: AsyncSession,
    server: ServerModel,
    check: ServerCheckSchema,
) -> None:
    last_dynamic_snapshot = (
        server.dynamic_snapshots[0] if server.dynamic_snapshots else None
    )

    need_new_dynamic = dynamic_snapshot_changed(
        last_dynamic_snapshot, check.server_dynamic_snapshot
    )

    if need_new_dynamic:
        last_dynamic_snapshot = ServerDynamicSnapshotModel(
            server=server,
            players_online=(check.server_dynamic_snapshot.players_online),
        )
        db.add(last_dynamic_snapshot)


def create_player_snapshot_if_changed(
    db: AsyncSession,
    player: PlayerModel,
    snapshot_schema: PlayerSnapshotSchema,
) -> PlayerSnapshotModel | None:
    last_player_snapshot = player.snapshots[0] if player.snapshots else None

    if not player_snapshot_changed(last_player_snapshot, snapshot_schema):
        return None

    player_snapshot = PlayerSnapshotModel(
        player=player,
        name=snapshot_schema.name,
        skin=snapshot_schema.skin,
        cape=snapshot_schema.cape,
    )
    db.add(player_snapshot)

    return player_snapshot


def handle_player_join(
    db: AsyncSession,
    player_map: dict[PlayerSchema, PlayerModel],
    server: ServerModel,
    player_schema: PlayerSchema,
    snapshot_schema: PlayerSnapshotSchema,
) -> PlayerModel:
    player = player_map.get(player_schema)

    # Player does not exist
    if player is None:
        player = PlayerModel(
            player_type=player_schema.player_type, uuid=player_schema.uuid
        )

        player_snapshot = PlayerSnapshotModel(
            player=player,
            name=snapshot_schema.name,
            skin=snapshot_schema.skin,
            cape=snapshot_schema.cape,
        )

        player_map[player_schema] = player
        db.add_all([player, player_snapshot])

    # Player does exist
    else:
        create_player_snapshot_if_changed(db, player, snapshot_schema)

        # Close previous session from another server if it is still open
        last_player_session = player.sessions[0] if player.sessions else None

        if last_player_session is not None and last_player_session.to is None:
            last_player_session.to = func.now()

    # Create new session on current server
    player_session = PlayerSessionModel(server=server, player=player)
    db.add(player_session)

    return player


def handle_players(
    db: AsyncSession,
    server: ServerModel,
    check: ServerCheckSchema,
    player_map: dict[PlayerSchema, PlayerModel],
) -> None:
    # 1. new player joined => save the new player + create new session for him
    # 2. if player left => close his sessions
    # 3. old player joined => create new session
    # 4. if nothing changed => do nothing

    active_sessions = {
        s.player.uuid: s for s in server.player_sessions if s.to is None
    }

    incoming_players = {p.uuid: (p, snap) for p, snap in check.players.items()}

    # players leaved the server
    for uuid, session in active_sessions.items():
        if uuid not in incoming_players:
            session.to = func.now()

    for uuid, (player_schema, snapshot_schema) in incoming_players.items():
        # if the player is already online than do nothing
        if uuid in active_sessions:
            continue

        # if player recently joined the server
        handle_player_join(
            db, player_map, server, player_schema, snapshot_schema
        )


def save_servers(
    db: AsyncSession,
    servers: list[tuple[ServerModel, ServerCheckSchema | None]],
    em: ExistingEntityMapsSchema,
) -> None:
    for server, check in servers:
        if handle_server_session(db, server, check) is None:
            continue  # server is offline

        handle_server_snapshot(
            db,
            server,
            check,  # type: ignore
            em.software_map,
            em.plugin_map,
            em.mod_map,
        )
        handle_dynamic_snapshot(db, server, check)  # type: ignore
        handle_players(db, server, check, em.player_map)  # type: ignore
