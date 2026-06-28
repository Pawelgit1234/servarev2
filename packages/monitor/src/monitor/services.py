from common.checks.ip import get_ip_info
from common.databases import ra
from common.enums import PlayerType
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
    ServerDynamicSnapshotModel,
    ServerModel,
    ServerSessionModel,
    ServerSnapshotModel,
)
from common.schemas.assets import ModSchema, PluginSchema, SoftwareSchema
from common.schemas.ip import IpInfoSchema
from common.schemas.server import (
    ServerCheckSchema,
)
from common.services.assets import (
    load_existing_mods,
    load_existing_plugins,
    load_existing_softwares,
)
from common.settings import (
    IP_CHECK_INTERVAL_DAYS,
    PORTER_CHECK_INTERVAL_DAYS,
    REDIS_PORTER_QUEUE,
)
from common.utils import has_expired
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, contains_eager

from monitor.utils import (
    dynamic_snapshot_changed,
    extract_assets_from_checks,
    need_create_server_snapshot,
    player_snapshot_changed,
)


async def get_next_server_group(
    db: AsyncSession,
) -> list[ServerModel]:
    ip_subquery = (
        select(ServerModel.ip)
        .order_by(ServerModel.last_seen_at.asc())
        .limit(1)
        .scalar_subquery()
    )

    updated_ids = (
        update(ServerModel)
        .where(ServerModel.ip == ip_subquery)
        .values(last_seen_at=func.now())
        .returning(ServerModel.id)
        .cte("updated_ids")
    )

    latest_snapshot = (
        select(ServerSnapshotModel)
        .distinct(ServerSnapshotModel.server_id)
        .order_by(
            ServerSnapshotModel.server_id,
            ServerSnapshotModel.created_at.desc(),
        )
        .subquery()
    )
    latest_snapshot_alias = aliased(ServerSnapshotModel, latest_snapshot)

    latest_dynamic_snapshot = (
        select(ServerDynamicSnapshotModel)
        .distinct(ServerDynamicSnapshotModel.server_id)
        .order_by(
            ServerDynamicSnapshotModel.server_id,
            ServerDynamicSnapshotModel.created_at.desc(),
        )
        .subquery()
    )
    latest_dynamic_snapshot_alias = aliased(
        ServerDynamicSnapshotModel,
        latest_dynamic_snapshot,
    )

    latest_session = (
        select(ServerSessionModel)
        .distinct(ServerSessionModel.server_id)
        .order_by(
            ServerSessionModel.server_id,
            ServerSessionModel.from_.desc(),
        )
        .subquery()
    )
    latest_session_alias = aliased(ServerSessionModel, latest_session)

    latest_player_session = (
        select(PlayerSessionModel)
        .join(PlayerModel, PlayerModel.id == PlayerSessionModel.player_id)
        .where(PlayerSessionModel.server_id == ServerModel.id)
        .distinct(PlayerModel.uuid)
        .order_by(
            PlayerModel.uuid,
            PlayerSessionModel.from_.desc(),
        )
        .correlate(ServerModel)
        .subquery()
    )
    latest_player_session_alias = aliased(
        PlayerSessionModel, latest_player_session
    )

    player_alias = aliased(PlayerModel)

    latest_player_snapshot = (
        select(PlayerSnapshotModel)
        .distinct(PlayerSnapshotModel.player_id)
        .order_by(
            PlayerSnapshotModel.player_id,
            PlayerSnapshotModel.created_at.desc(),
        )
        .subquery()
    )
    latest_player_snapshot_alias = aliased(
        PlayerSnapshotModel, latest_player_snapshot
    )

    stmt = (
        select(ServerModel)
        .where(ServerModel.id.in_(select(updated_ids.c.id)))
        .outerjoin(
            latest_snapshot_alias,
            latest_snapshot_alias.server_id == ServerModel.id,
        )
        .outerjoin(
            latest_dynamic_snapshot_alias,
            latest_dynamic_snapshot_alias.server_id == ServerModel.id,
        )
        .outerjoin(
            latest_session_alias,
            latest_session_alias.server_id == ServerModel.id,
        )
        .outerjoin(
            latest_player_session_alias,
            latest_player_session_alias.server_id == ServerModel.id,
        )
        .outerjoin(
            player_alias,
            player_alias.id == latest_player_session_alias.player_id,
        )
        .outerjoin(
            latest_player_snapshot_alias,
            latest_player_snapshot_alias.player_id == player_alias.id,
        )
        .options(
            contains_eager(
                ServerModel.snapshots, alias=latest_snapshot_alias
            ).selectinload(ServerSnapshotModel.software),
            contains_eager(ServerModel.snapshots, alias=latest_snapshot_alias)
            .selectinload(ServerSnapshotModel.plugin_associations)
            .selectinload(ServerSnapshotPluginAssociationModel.plugin),
            contains_eager(ServerModel.snapshots, alias=latest_snapshot_alias)
            .selectinload(ServerSnapshotModel.mod_associations)
            .selectinload(ServerSnapshotModAssociationModel.mod),
            contains_eager(
                ServerModel.dynamic_snapshots,
                alias=latest_dynamic_snapshot_alias,
            ),
            contains_eager(ServerModel.sessions, alias=latest_session_alias),
            contains_eager(
                ServerModel.player_sessions, alias=latest_player_session_alias
            )
            .contains_eager(PlayerSessionModel.player, alias=player_alias)
            .contains_eager(
                PlayerModel.snapshots, alias=latest_player_snapshot_alias
            ),
        )
    )

    servers = (await db.execute(stmt)).scalars().unique().all()

    return servers  # type: ignore


async def prepare_ip_data(
    server_model: ServerModel,
) -> tuple[IpInfoSchema | None, bool]:
    ip_info = None
    update_porter = False

    if has_expired(
        server_model.last_ip_check_at,
        IP_CHECK_INTERVAL_DAYS,  # type: ignore
    ):
        ip_info = await get_ip_info(server_model.ip)

    if (
        has_expired(
            server_model.last_porter_check_at,
            PORTER_CHECK_INTERVAL_DAYS,  # type: ignore
        )
        and not server_model.is_multiport
    ):
        await ra.rpush(REDIS_PORTER_QUEUE, server_model.ip)  # type: ignore
        update_porter = True

    return ip_info, update_porter


def handle_ip_info_and_porter(
    server: ServerModel,
    ip_info: IpInfoSchema | None,
    update_porter: bool,
) -> None:
    if ip_info is not None and ip_info.country is not None:
        server.last_ip_check_at = func.now()

        server.country = ip_info.country
        server.region = ip_info.region
        server.city = ip_info.city
        server.latitude = ip_info.latitude
        server.longitude = ip_info.longitude
        server.hostname = ip_info.hostname
        server.asn = ip_info.asn

    if update_porter:
        server.last_porter_check_at = func.now()


def handle_server_session(
    db: AsyncSession,
    server: ServerModel,
    check: ServerCheckSchema | None,
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

        software = software_map.get(check.software)
        if software is None:
            software = SoftwareModel(
                name=check.software.name,
                version=check.software.version,
            )
            software_map[check.software] = software
            db.add(software)
        new_snapshot.software = software  # type: ignore

        # == Plugins ==
        for p in check.plugins:
            plugin = plugin_map.get(p)

            if plugin is None:
                plugin = PluginModel(name=p.name)
                plugin_map[p] = plugin
                db.add(plugin)
            new_snapshot.plugin_associations.append(
                ServerSnapshotPluginAssociationModel(plugin=plugin)
            )

        # == Mods ==
        for m in check.mods:
            mod = mod_map.get(m)

            if mod is None:
                mod = ModModel(name=m.name, version=m.version)
                mod_map[m] = mod
                db.add(mod)
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


def handle_players(
    db: AsyncSession,
    server: ServerModel,
    check: ServerCheckSchema,
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
        # if player was already online, do nothing
        # =else=> player comed to the server
        player_session = active_sessions.get(uuid)
        if player_session is not None:
            continue

        # looks if player is at least in db
        player = None
        for s in server.player_sessions:
            if s.player.uuid == uuid:
                player = s.player
                break

        # if not => save to db
        if player is None:
            player = PlayerModel(
                uuid=uuid, player_type=player_schema.player_type
            )
            player_snapshot = PlayerSnapshotModel(
                player=player,
                name=snapshot_schema.name,
                skin=snapshot_schema.skin,
                cape=snapshot_schema.cape,
            )

            db.add(player)
            db.add(player_snapshot)

        # updates player snapshots => assumes that the player cannot change
        # the skin during the playing and is not new on the server
        elif player_schema.player_type == PlayerType.PREMIUM:
            last_player_snapshot = (
                player.snapshots[0] if player.snapshots else None
            )

            need_new_player_snapshot = player_snapshot_changed(
                last_player_snapshot, snapshot_schema
            )

            if need_new_player_snapshot:
                new_player_snapshot = PlayerSnapshotModel(
                    player=player,
                    name=snapshot_schema.name,
                    skin=snapshot_schema.skin,
                    cape=snapshot_schema.cape,
                )

                db.add(new_player_snapshot)

        new_player_session = PlayerSessionModel(player=player, server=server)
        db.add(new_player_session)


async def save_servers(
    db: AsyncSession,
    servers: list[tuple[ServerModel, ServerCheckSchema | None]],
    ip_info: IpInfoSchema | None,
    update_porter: bool,
) -> None:

    # collects all incoming softwares/plugins/mods from batch
    all_softwares, all_plugins, all_mods = extract_assets_from_checks(servers)
    software_map = await load_existing_softwares(db, all_softwares)
    plugin_map = await load_existing_plugins(db, all_plugins)
    mod_map = await load_existing_mods(db, all_mods)

    for server, check in servers:
        handle_ip_info_and_porter(server, ip_info, update_porter)

        if handle_server_session(db, server, check) is None:
            continue

        assert check is not None  # only for mypy

        handle_server_snapshot(
            db, server, check, software_map, plugin_map, mod_map
        )
        handle_dynamic_snapshot(db, server, check)
        handle_players(db, server, check)
