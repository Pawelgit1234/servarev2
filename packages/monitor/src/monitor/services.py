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
from common.schemas.player import PlayerSnapshotSchema
from common.schemas.server import (
    ServerCheckSchema,
    ServerDynamicSnapshotSchema,
    ServerSnapshotSchema,
)
from sqlalchemy import func, select, tuple_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


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

    latest_server_snapshot_id = (
        select(ServerSnapshotModel.id)
        .where(ServerSnapshotModel.server_id == ServerModel.id)
        .order_by(ServerSnapshotModel.created_at.desc())
        .limit(1)
        .scalar_subquery()
    )

    latest_dynamic_snapshot_id = (
        select(ServerDynamicSnapshotModel.id)
        .where(ServerDynamicSnapshotModel.server_id == ServerModel.id)
        .order_by(ServerDynamicSnapshotModel.created_at.desc())
        .limit(1)
        .scalar_subquery()
    )

    latest_server_session_id = (
        select(ServerSessionModel.id)
        .where(ServerSessionModel.server_id == ServerModel.id)
        .order_by(ServerSessionModel.from_.desc())
        .limit(1)
        .scalar_subquery()
    )

    # newest player session per uuid on current server
    latest_player_session_ids = (
        select(PlayerSessionModel.id)
        .join(PlayerModel, PlayerModel.id == PlayerSessionModel.player_id)
        .where(PlayerSessionModel.server_id == ServerModel.id)
        .distinct(PlayerModel.uuid)
        .order_by(
            PlayerModel.uuid,
            PlayerSessionModel.from_.desc(),
        )
        .correlate(ServerModel)
    )

    stmt = (
        select(ServerModel)
        .join(updated_ids, ServerModel.id == updated_ids.c.id)
        .options(
            # newest server snapshot only + software/plugins/mods
            selectinload(
                ServerModel.snapshots.and_(
                    ServerSnapshotModel.id == latest_server_snapshot_id
                )
            ).selectinload(ServerSnapshotModel.software),
            selectinload(
                ServerModel.snapshots.and_(
                    ServerSnapshotModel.id == latest_server_snapshot_id
                )
            )
            .selectinload(ServerSnapshotModel.plugin_associations)
            .selectinload(ServerSnapshotPluginAssociationModel.plugin),
            selectinload(
                ServerModel.snapshots.and_(
                    ServerSnapshotModel.id == latest_server_snapshot_id
                )
            )
            .selectinload(ServerSnapshotModel.mod_associations)
            .selectinload(ServerSnapshotModAssociationModel.mod),
            # newest dynamic snapshot only
            selectinload(
                ServerModel.dynamic_snapshots.and_(
                    ServerDynamicSnapshotModel.id == latest_dynamic_snapshot_id
                )
            ),
            # newest server session only
            selectinload(
                ServerModel.sessions.and_(
                    ServerSessionModel.id == latest_server_session_id
                )
            ),
            # newest player session per unique uuid
            selectinload(
                ServerModel.player_sessions.and_(
                    PlayerSessionModel.id.in_(latest_player_session_ids)
                )
            )
            .selectinload(PlayerSessionModel.player)
            .selectinload(PlayerModel.snapshots),
        )
    )

    servers = (await db.execute(stmt)).scalars().unique().all()

    return servers  # type: ignore


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


async def save_servers(
    db: AsyncSession,
    servers: list[tuple[ServerModel, ServerCheckSchema | None]],
    ip_info: IpInfoSchema,
    update_ip: bool,
    update_porter: bool,
) -> None:

    # collects all incoming softwares/plugins/mods from batch
    all_softwares = {
        (check.software.name, check.software.version)
        for _, check in servers
        if check
    }
    all_plugins = {
        p.name for _, check in servers if check for p in check.plugins
    }
    all_mods = {
        (m.name, m.version)
        for _, check in servers
        if check
        for m in check.mods
    }

    # preload existing in DB
    existing_softwares = (
        (
            await db.execute(
                select(SoftwareModel).where(
                    tuple_(SoftwareModel.name, SoftwareModel.version).in_(
                        all_softwares
                    )
                )
            )
        )
        .scalars()
        .all()
    )

    existing_plugins = (
        (
            await db.execute(
                select(PluginModel).where(PluginModel.name.in_(all_plugins))
            )
        )
        .scalars()
        .all()
    )

    existing_mods = (
        (
            await db.execute(
                select(ModModel).where(
                    tuple_(ModModel.name, ModModel.version).in_(all_mods)
                )
            )
        )
        .scalars()
        .all()
    )

    software_map = {(s.name, s.version): s for s in existing_softwares}
    plugin_map = {p.name: p for p in existing_plugins}
    mod_map = {(m.name, m.version): m for m in existing_mods}

    for server, check in servers:
        if update_ip:
            server.last_ip_check_at = func.now()
        if update_porter:
            server.last_porter_check_at = func.now()

        if ip_info.country is not None:
            server.country = ip_info.country
            server.region = ip_info.region
            server.city = ip_info.city
            server.latitude = ip_info.latitude
            server.longitude = ip_info.longitude
            server.hostname = ip_info.hostname
            server.asn = ip_info.asn

        # == Session ==
        last_session = server.sessions[0] if server.sessions else None

        # server inactive
        if check is None:
            if last_session is not None and last_session.to is None:
                last_session.to = func.now()
            continue

        # server active
        if last_session is None or last_session.to is not None:
            new_session = ServerSessionModel(server=server)
            db.add(new_session)

        # == Snapshot ==

        # checks if there is any difference between
        # last snapshot and check´s snapshot
        last_snapshot = server.snapshots[0] if server.snapshots else None
        last_software = last_snapshot.software if last_snapshot else None
        last_plugins = [
            assoc.plugin
            for assoc in (
                last_snapshot.plugin_associations if last_snapshot else []
            )
        ]
        last_mods = [
            assoc.mod
            for assoc in (
                last_snapshot.mod_associations if last_snapshot else []
            )
        ]

        need_new_snapshot = any(
            (
                snapshot_changed(last_snapshot, check.server_snapshot),
                software_changed(last_software, check.software),
                plugins_changed(last_plugins, check.plugins),
                mods_changed(last_mods, check.mods),
            )
        )

        if need_new_snapshot:
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

            # last software is already in software_map (plugins and mods too)
            software_key = (check.software.name, check.software.version)
            software = software_map.get(software_key)

            if software is None:
                software = SoftwareModel(
                    name=check.software.name,
                    version=check.software.version,
                )
                software_map[software_key] = software
                db.add(software)
            new_snapshot.software = software  # type: ignore

            # == Plugins ==
            for p in check.plugins:
                plugin = plugin_map.get(p.name)

                if plugin is None:
                    plugin = PluginModel(name=p.name)
                    plugin_map[p.name] = plugin
                    db.add(plugin)
                new_snapshot.plugin_associations.append(
                    ServerSnapshotPluginAssociationModel(plugin=plugin)
                )

            # == Mods ==
            for m in check.mods:
                mod_key = (m.name, m.version)
                mod = mod_map.get(mod_key)

                if mod is None:
                    mod = ModModel(name=m.name, version=m.version)
                    mod_map[mod_key] = mod
                    db.add(mod)
                new_snapshot.mod_associations.append(
                    ServerSnapshotModAssociationModel(mod=mod)
                )

        # == Dynamic Snapshot ==
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

        # == Players ==

        # 1. new players joined => save + create new session for them
        # 2. if players left => close their sessions
        # 3. if players joined again => create new sessions
        # 4. if nothing changed => do nothing

        active_sessions = {
            s.player.uuid: s for s in server.player_sessions if s.to is None
        }

        incoming_players = {
            p.uuid: (p, snap) for p, snap in check.players.items()
        }

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
                    uuid=uuid,
                    player_type=player_schema.player_type,
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

            new_player_session = PlayerSessionModel(
                player=player,
                server=server,
            )
            db.add(new_player_session)
