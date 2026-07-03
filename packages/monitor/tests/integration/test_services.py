from datetime import UTC, datetime

import pytest
from common.enums import PlayerType, ServerSoftwareType, ServerType
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
from common.schemas.player import PlayerSchema, PlayerSnapshotSchema
from common.schemas.server import (
    ServerCheckSchema,
    ServerDynamicSnapshotSchema,
    ServerSchema,
    ServerSnapshotSchema,
)
from common.services.assets import (
    load_existing_mods,
    load_existing_plugins,
    load_existing_softwares,
)
from monitor.services import (
    get_next_server_group,
    handle_players,
    handle_server_session,
    handle_server_snapshot,
)
from monitor.utils import extract_assets_from_servers
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


# == Tests for "get_next_server_group" ==
@pytest.mark.asyncio
async def test_get_next_server_group_servers_last_seen_change(
    db: AsyncSession,
) -> None:
    s1 = ServerModel(
        ip="1.1.1.1",
        port=25565,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
        last_seen_at=datetime(2000, 1, 1, 1, 1, 1),
    )
    s2 = ServerModel(
        ip="1.1.1.1",
        port=25566,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
        last_seen_at=datetime(2000, 1, 1, 1, 1, 2),
    )
    s3 = ServerModel(
        ip="1.1.1.2",
        port=25565,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
        last_seen_at=datetime(2000, 1, 1, 1, 1, 3),
    )
    s4 = ServerModel(
        ip="1.1.1.3",
        port=25565,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
        last_seen_at=datetime(2000, 1, 1, 1, 1, 4),
    )

    db.add_all([s1, s2, s3, s4])
    await db.commit()

    db.expire_all()  # very important!

    servers = await get_next_server_group(db)
    assert len(servers) == 2

    servers = await get_next_server_group(db)
    assert len(servers) == 1

    servers = await get_next_server_group(db)
    assert len(servers) == 1

    servers = await get_next_server_group(db)
    assert len(servers) == 2


@pytest.mark.asyncio
async def test_get_next_server_group_only_latest_snapshots_one_server(
    db: AsyncSession,
) -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25565,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
    )
    db.add(server)

    old_snapshot = ServerSnapshotModel(
        server=server,
        version="1.19",
        players_max=20,
        motd="old",
        latency=1,
        created_at=datetime(2000, 1, 1, 1, 1, 1),
    )

    new_snapshot = ServerSnapshotModel(
        server=server,
        version="1.20",
        players_max=100,
        motd="new",
        latency=1,
        created_at=datetime(2000, 1, 1, 1, 1, 2),
    )

    db.add_all([old_snapshot, new_snapshot])
    await db.commit()

    db.expire_all()  # very important!

    servers = await get_next_server_group(db)
    assert len(servers) == 1

    loaded_server = servers[0]
    assert len(loaded_server.snapshots) == 1
    assert loaded_server.snapshots[0].version == "1.20"


@pytest.mark.asyncio
async def test_get_next_server_group_only_latest_snapshots_two_servers(
    db: AsyncSession,
) -> None:
    s1 = ServerModel(
        ip="1.1.1.1",
        port=25565,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
    )
    s1_old = ServerSnapshotModel(
        server=s1,
        version="1.19",
        players_max=20,
        motd="s1_old",
        latency=1,
        created_at=datetime(2000, 1, 1, 1, 1, 1),
    )
    s1_new = ServerSnapshotModel(
        server=s1,
        version="1.20",
        players_max=100,
        motd="s1_new",
        latency=1,
        created_at=datetime(2000, 1, 1, 1, 1, 2),
    )

    s2 = ServerModel(
        ip="1.1.1.1",
        port=25566,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
    )
    s2_old = ServerSnapshotModel(
        server=s2,
        version="1.19",
        players_max=20,
        motd="s2_old",
        latency=1,
        created_at=datetime(2000, 1, 1, 1, 1, 1),
    )
    s2_new = ServerSnapshotModel(
        server=s2,
        version="1.20",
        players_max=100,
        motd="s2_new",
        latency=1,
        created_at=datetime(2000, 1, 1, 1, 1, 2),
    )

    db.add_all([s1, s1_old, s1_new, s2, s2_old, s2_new])
    await db.commit()

    db.expire_all()  # very important!

    servers = await get_next_server_group(db)

    assert len(servers) == 2

    servers_by_port = {s.port: s for s in servers}

    assert 25565 in servers_by_port
    assert 25566 in servers_by_port

    loaded_s1 = servers_by_port[25565]
    assert len(loaded_s1.snapshots) == 1
    assert loaded_s1.snapshots[0].version == "1.20"
    assert loaded_s1.snapshots[0].motd == "s1_new"

    loaded_s2 = servers_by_port[25566]
    assert len(loaded_s2.snapshots) == 1
    assert loaded_s2.snapshots[0].version == "1.20"
    assert loaded_s2.snapshots[0].motd == "s2_new"


@pytest.mark.asyncio
async def test_get_next_server_group_only_latest_dynamic_snapshots_one_server(
    db: AsyncSession,
) -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25565,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
    )
    db.add(server)

    old_dynamic_snapshot = ServerDynamicSnapshotModel(
        server=server,
        players_online=1,
        created_at=datetime(2000, 1, 1, 1, 1, 1),
    )
    new_dynamic_snapshot = ServerDynamicSnapshotModel(
        server=server,
        players_online=2,
        created_at=datetime(2000, 1, 1, 1, 1, 2),
    )

    db.add_all([old_dynamic_snapshot, new_dynamic_snapshot])
    await db.commit()

    db.expire_all()  # very important!

    servers = await get_next_server_group(db)

    assert len(servers) == 1

    loaded_server = servers[0]
    assert len(loaded_server.dynamic_snapshots) == 1
    assert loaded_server.dynamic_snapshots[0].players_online == 2


@pytest.mark.asyncio
async def test_get_next_server_group_only_latest_dynamic_snapshots_two_servers(
    db: AsyncSession,
) -> None:
    s1 = ServerModel(
        ip="1.1.1.1",
        port=25565,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
    )
    s1_old = ServerDynamicSnapshotModel(
        server=s1,
        players_online=1,
        created_at=datetime(2000, 1, 1, 1, 1, 1),
    )
    s1_new = ServerDynamicSnapshotModel(
        server=s1,
        players_online=2,
        created_at=datetime(2000, 1, 1, 1, 1, 2),
    )

    s2 = ServerModel(
        ip="1.1.1.1",
        port=25566,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
    )
    s2_old = ServerDynamicSnapshotModel(
        server=s2,
        players_online=10,
        created_at=datetime(2000, 1, 1, 1, 1, 1),
    )
    s2_new = ServerDynamicSnapshotModel(
        server=s2,
        players_online=20,
        created_at=datetime(2000, 1, 1, 1, 1, 2),
    )

    db.add_all([s1, s1_old, s1_new, s2, s2_old, s2_new])
    await db.commit()

    db.expire_all()  # very important!

    servers = await get_next_server_group(db)

    assert len(servers) == 2

    servers_by_port = {s.port: s for s in servers}

    assert 25565 in servers_by_port
    assert 25566 in servers_by_port

    loaded_s1 = servers_by_port[25565]
    assert len(loaded_s1.dynamic_snapshots) == 1
    assert loaded_s1.dynamic_snapshots[0].players_online == 2

    loaded_s2 = servers_by_port[25566]
    assert len(loaded_s2.dynamic_snapshots) == 1
    assert loaded_s2.dynamic_snapshots[0].players_online == 20


@pytest.mark.asyncio
async def test_get_next_server_group_only_latest_server_session_one_server(
    db: AsyncSession,
) -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25565,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
    )
    db.add(server)

    old_session = ServerSessionModel(
        server=server,
        from_=datetime(2000, 1, 1, 1, 1, 1),
        to=datetime(2000, 1, 1, 1, 1, 2),
    )
    new_session = ServerSessionModel(
        server=server,
        from_=datetime(2000, 1, 1, 1, 1, 3),
        to=None,
    )

    db.add_all([old_session, new_session])
    await db.commit()

    db.expire_all()  # very important!

    servers = await get_next_server_group(db)

    assert len(servers) == 1

    loaded_server = servers[0]
    assert len(loaded_server.sessions) == 1
    assert loaded_server.sessions[0].from_ == datetime(
        2000, 1, 1, 1, 1, 3, tzinfo=UTC
    )
    assert loaded_server.sessions[0].to is None


@pytest.mark.asyncio
async def test_get_next_server_group_only_latest_server_session_two_servers(
    db: AsyncSession,
) -> None:
    s1 = ServerModel(
        ip="1.1.1.1",
        port=25565,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
    )
    s1_old = ServerSessionModel(
        server=s1,
        from_=datetime(2000, 1, 1, 1, 1, 1),
        to=datetime(2000, 1, 1, 1, 1, 2),
    )
    s1_new = ServerSessionModel(
        server=s1,
        from_=datetime(2000, 1, 1, 1, 1, 3),
        to=None,
    )

    s2 = ServerModel(
        ip="1.1.1.1",
        port=25566,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
    )
    s2_old = ServerSessionModel(
        server=s2,
        from_=datetime(2000, 1, 1, 1, 1, 1),
        to=datetime(2000, 1, 1, 1, 1, 2),
    )
    s2_new = ServerSessionModel(
        server=s2,
        from_=datetime(2000, 1, 1, 1, 1, 4),
        to=None,
    )

    db.add_all([s1, s1_old, s1_new, s2, s2_old, s2_new])
    await db.commit()

    db.expire_all()  # very important!

    servers = await get_next_server_group(db)

    assert len(servers) == 2

    servers_by_port = {s.port: s for s in servers}

    assert 25565 in servers_by_port
    assert 25566 in servers_by_port

    loaded_s1 = servers_by_port[25565]
    assert len(loaded_s1.sessions) == 1
    assert loaded_s1.sessions[0].from_ == datetime(
        2000, 1, 1, 1, 1, 3, tzinfo=UTC
    )
    assert loaded_s1.sessions[0].to is None

    loaded_s2 = servers_by_port[25566]
    assert len(loaded_s2.sessions) == 1
    assert loaded_s2.sessions[0].from_ == datetime(
        2000, 1, 1, 1, 1, 4, tzinfo=UTC
    )
    assert loaded_s2.sessions[0].to is None


async def test_get_next_server_group_players_one_server(
    db: AsyncSession,
) -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25565,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
    )
    db.add(server)

    p1 = PlayerModel(
        player_type=PlayerType.PREMIUM,
        uuid="11111111-1111-1111-1111-111111111111",
    )
    p1_session_old = PlayerSessionModel(
        server=server,
        player=p1,
        from_=datetime(2000, 1, 1, 1, 1, 1),
        to=datetime(2000, 1, 1, 1, 1, 2),
    )
    p1_session_new = PlayerSessionModel(
        server=server, player=p1, from_=datetime(2000, 1, 1, 1, 1, 3), to=None
    )
    p1_snapshot_old = PlayerSnapshotModel(
        player=p1,
        name="p1_old",
        skin=None,
        cape=None,
        created_at=datetime(2000, 1, 1, 1, 1, 1),
    )
    p1_snapshot_new = PlayerSnapshotModel(
        player=p1,
        name="p1_new",
        skin=None,
        cape=None,
        created_at=datetime(2000, 1, 1, 1, 1, 2),
    )

    p2 = PlayerModel(
        player_type=PlayerType.PREMIUM,
        uuid="22222222-2222-2222-2222-222222222222",
    )
    p2_session_old = PlayerSessionModel(
        server=server,
        player=p2,
        from_=datetime(2000, 1, 1, 1, 1, 1),
        to=datetime(2000, 1, 1, 1, 1, 2),
    )
    p2_session_new = PlayerSessionModel(
        server=server, player=p2, from_=datetime(2000, 1, 1, 1, 1, 3), to=None
    )
    p2_snapshot_old = PlayerSnapshotModel(
        player=p2,
        name="p2_old",
        skin=None,
        cape=None,
        created_at=datetime(2000, 1, 1, 1, 1, 1),
    )
    p2_snapshot_new = PlayerSnapshotModel(
        player=p2,
        name="p2_new",
        skin=None,
        cape=None,
        created_at=datetime(2000, 1, 1, 1, 1, 2),
    )

    db.add_all(
        [
            p1,
            p1_session_old,
            p1_session_new,
            p1_snapshot_old,
            p1_snapshot_new,
            p2,
            p2_session_old,
            p2_session_new,
            p2_snapshot_old,
            p2_snapshot_new,
        ]
    )
    await db.commit()

    db.expire_all()  # very important!

    servers = await get_next_server_group(db)
    assert len(servers) == 1

    loaded_server = servers[0]
    assert len(loaded_server.player_sessions) == 2

    sessions_by_uuid = {
        session.player.uuid: session
        for session in loaded_server.player_sessions
    }

    assert "11111111-1111-1111-1111-111111111111" in sessions_by_uuid
    s1 = sessions_by_uuid["11111111-1111-1111-1111-111111111111"]
    assert s1.from_ == datetime(2000, 1, 1, 1, 1, 3, tzinfo=UTC)
    assert s1.to is None

    assert len(s1.player.snapshots) == 1
    assert s1.player.snapshots[0].name == "p1_new"

    assert "22222222-2222-2222-2222-222222222222" in sessions_by_uuid
    s2 = sessions_by_uuid["22222222-2222-2222-2222-222222222222"]
    assert s2.from_ == datetime(2000, 1, 1, 1, 1, 3, tzinfo=UTC)
    assert s2.to is None

    assert len(s2.player.snapshots) == 1
    assert s2.player.snapshots[0].name == "p2_new"


@pytest.mark.asyncio
async def test_get_next_server_group_players_two_servers(
    db: AsyncSession,
) -> None:
    s1 = ServerModel(
        ip="1.1.1.1",
        port=25565,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
    )
    s1_p1 = PlayerModel(
        player_type=PlayerType.PREMIUM,
        uuid="11111111-1111-1111-1111-111111111111",
    )
    s1_p1_session_old = PlayerSessionModel(
        server=s1,
        player=s1_p1,
        from_=datetime(2000, 1, 1, 1, 1, 1),
        to=datetime(2000, 1, 1, 1, 1, 2),
    )
    s1_p1_session_new = PlayerSessionModel(
        server=s1,
        player=s1_p1,
        from_=datetime(2000, 1, 1, 1, 1, 3),
        to=None,
    )
    s1_p1_snapshot_old = PlayerSnapshotModel(
        player=s1_p1,
        name="p1_old",
        skin=None,
        cape=None,
        created_at=datetime(2000, 1, 1, 1, 1, 1),
    )
    s1_p1_snapshot_new = PlayerSnapshotModel(
        player=s1_p1,
        name="p1_new",
        skin=None,
        cape=None,
        created_at=datetime(2000, 1, 1, 1, 1, 2),
    )

    s1_p2 = PlayerModel(
        player_type=PlayerType.PREMIUM,
        uuid="22222222-2222-2222-2222-222222222222",
    )
    s1_p2_session_old = PlayerSessionModel(
        server=s1,
        player=s1_p2,
        from_=datetime(2000, 1, 1, 1, 1, 1),
        to=datetime(2000, 1, 1, 1, 1, 2),
    )
    s1_p2_session_new = PlayerSessionModel(
        server=s1,
        player=s1_p2,
        from_=datetime(2000, 1, 1, 1, 1, 3),
        to=None,
    )
    s1_p2_snapshot_old = PlayerSnapshotModel(
        player=s1_p2,
        name="p2_old",
        skin=None,
        cape=None,
        created_at=datetime(2000, 1, 1, 1, 1, 1),
    )
    s1_p2_snapshot_new = PlayerSnapshotModel(
        player=s1_p2,
        name="p2_new",
        skin=None,
        cape=None,
        created_at=datetime(2000, 1, 1, 1, 1, 2),
    )

    s2 = ServerModel(
        ip="1.1.1.1",
        port=25566,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
    )
    s2_p1 = PlayerModel(
        player_type=PlayerType.PREMIUM,
        uuid="33333333-3333-3333-3333-333333333333",
    )
    s2_p1_session_old = PlayerSessionModel(
        server=s2,
        player=s2_p1,
        from_=datetime(2000, 1, 1, 1, 1, 1),
        to=datetime(2000, 1, 1, 1, 1, 2),
    )
    s2_p1_session_new = PlayerSessionModel(
        server=s2,
        player=s2_p1,
        from_=datetime(2000, 1, 1, 1, 1, 3),
        to=None,
    )
    s2_p1_snapshot_old = PlayerSnapshotModel(
        player=s2_p1,
        name="p3_old",
        skin=None,
        cape=None,
        created_at=datetime(2000, 1, 1, 1, 1, 1),
    )
    s2_p1_snapshot_new = PlayerSnapshotModel(
        player=s2_p1,
        name="p3_new",
        skin=None,
        cape=None,
        created_at=datetime(2000, 1, 1, 1, 1, 2),
    )

    db.add_all(
        [
            s1,
            s1_p1,
            s1_p1_session_old,
            s1_p1_session_new,
            s1_p1_snapshot_old,
            s1_p1_snapshot_new,
            s1_p2,
            s1_p2_session_old,
            s1_p2_session_new,
            s1_p2_snapshot_old,
            s1_p2_snapshot_new,
            s2,
            s2_p1,
            s2_p1_session_old,
            s2_p1_session_new,
            s2_p1_snapshot_old,
            s2_p1_snapshot_new,
        ]
    )

    await db.commit()
    db.expire_all()

    servers = await get_next_server_group(db)

    assert len(servers) == 2

    servers_by_port = {s.port: s for s in servers}

    assert 25565 in servers_by_port
    assert 25566 in servers_by_port

    s1_loaded = servers_by_port[25565]
    assert len(s1_loaded.player_sessions) == 2

    s1_sessions = {s.player.uuid: s for s in s1_loaded.player_sessions}

    assert (
        len(
            s1_sessions[
                "11111111-1111-1111-1111-111111111111"
            ].player.snapshots
        )
        == 1
    )
    assert (
        s1_sessions["11111111-1111-1111-1111-111111111111"]
        .player.snapshots[0]
        .name
        == "p1_new"
    )

    assert (
        len(
            s1_sessions[
                "22222222-2222-2222-2222-222222222222"
            ].player.snapshots
        )
        == 1
    )
    assert (
        s1_sessions["22222222-2222-2222-2222-222222222222"]
        .player.snapshots[0]
        .name
        == "p2_new"
    )

    s2_loaded = servers_by_port[25566]
    assert len(s2_loaded.player_sessions) == 1

    s2_session = s2_loaded.player_sessions[0]
    assert s2_session.player.uuid == "33333333-3333-3333-3333-333333333333"
    assert len(s2_session.player.snapshots) == 1
    assert s2_session.player.snapshots[0].name == "p3_new"


# === Tests for "handle_server_session" ===
@pytest.mark.asyncio
async def test_handle_server_session_inactive_closes_open_session(
    db: AsyncSession,
) -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25565,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
    )

    session = ServerSessionModel(
        server=server,
        from_=datetime(2000, 1, 1, 1, 1, 1),
        to=None,
    )

    db.add_all([server, session])
    await db.commit()

    session_id = session.id

    db.expire_all()

    server = (await get_next_server_group(db))[0]
    result = handle_server_session(db=db, server=server, check=None)

    await db.commit()
    db.expire_all()

    assert result is None

    # reload session from DB
    refreshed = await db.get(ServerSessionModel, session_id)
    assert refreshed.to is not None  # type: ignore


@pytest.mark.asyncio
async def test_handle_server_session_inactive_no_open_session(
    db: AsyncSession,
) -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25565,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
    )

    db.add(server)
    await db.commit()

    server = (await get_next_server_group(db))[0]
    server_id = server.id

    result = handle_server_session(db=db, server=server, check=None)

    await db.commit()
    db.expire_all()

    assert result is None

    sessions = await db.execute(
        select(ServerSessionModel).where(
            ServerSessionModel.server_id == server_id
        )
    )

    assert len(sessions.scalars().all()) == 0


async def test_handle_server_session_active_creates_new_session(
    db: AsyncSession,
) -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25565,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
    )

    db.add(server)
    await db.commit()

    server = (await get_next_server_group(db))[0]

    check = ServerCheckSchema.model_construct()
    result = handle_server_session(db=db, server=server, check=check)

    await db.commit()
    server_id = server.id

    db.expire_all()

    assert isinstance(result, ServerSessionModel)

    sessions = await db.execute(
        select(ServerSessionModel).where(
            ServerSessionModel.server_id == server_id
        )
    )

    assert len(sessions.scalars().all()) == 1


async def test_handle_server_session_active_returns_open_session(
    db: AsyncSession,
) -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25565,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
    )

    session = ServerSessionModel(
        server=server,
        from_=datetime(2000, 1, 1, 1, 1, 1),
        to=None,
    )

    check = ServerCheckSchema.model_construct()

    db.add_all([server, session])
    await db.commit()

    server = (await get_next_server_group(db))[0]

    result = handle_server_session(db=db, server=server, check=check)

    await db.commit()
    server_id = server.id
    session_id = session.id
    result_id = result.id  # type: ignore
    db.expire_all()

    assert result_id == session_id

    sessions = await db.execute(
        select(ServerSessionModel).where(
            ServerSessionModel.server_id == server_id
        )
    )

    assert len(sessions.scalars().all()) == 1


# == Tests for "handle_players" ==


async def test_handle_players_new_player_joined(
    db: AsyncSession,
) -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25565,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
    )

    db.add(server)
    await db.commit()

    player_schema = PlayerSchema(
        uuid="11111111-1111-1111-1111-111111111111",
        player_type=PlayerType.PREMIUM,
    )

    snapshot_schema = PlayerSnapshotSchema(
        name="Steve",
        skin="skin1",
        cape="cape1",
    )

    check = ServerCheckSchema.model_construct(
        players={player_schema: snapshot_schema},
    )

    server = (await get_next_server_group(db))[0]
    handle_players(db, server, check)

    await db.commit()
    db.expire_all()

    player = await db.scalar(
        select(PlayerModel)
        .where(PlayerModel.uuid == player_schema.uuid)
        .options(selectinload(PlayerModel.snapshots))
    )

    server = (await get_next_server_group(db))[0]

    assert player is not None
    assert len(player.snapshots) == 1
    assert len(server.player_sessions) == 1


async def test_handle_players_player_left(
    db: AsyncSession,
) -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25565,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
    )

    player = PlayerModel(
        uuid="11111111-1111-1111-1111-111111111111",
        player_type=PlayerType.PREMIUM,
    )

    session = PlayerSessionModel(
        player=player,
        server=server,
        from_=datetime(2000, 1, 1),
        to=None,
    )

    db.add_all([server, player, session])
    await db.commit()

    session_id = session.id

    check = ServerCheckSchema.model_construct(players={})

    server = (await get_next_server_group(db))[0]
    handle_players(db, server, check)

    await db.commit()
    db.expire_all()

    refreshed = await db.get(PlayerSessionModel, session_id)

    assert refreshed is not None
    assert refreshed.to is not None


async def test_handle_players_old_player_joined(
    db: AsyncSession,
) -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25565,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
    )

    player = PlayerModel(
        uuid="11111111-1111-1111-1111-111111111111",
        player_type=PlayerType.PREMIUM,
    )

    snapshot = PlayerSnapshotModel(
        player=player,
        name="Steve",
        skin="skin1",
        cape="cape1",
    )

    old_session = PlayerSessionModel(
        player=player,
        server=server,
        from_=datetime(2000, 1, 1),
        to=datetime(2000, 1, 2),
    )

    db.add_all([server, player, snapshot, old_session])
    await db.commit()

    player_schema = PlayerSchema(
        uuid=player.uuid,
        player_type=PlayerType.PREMIUM,
    )

    snapshot_schema = PlayerSnapshotSchema(
        name="Steve",
        skin="skin1",
        cape="cape1",
    )

    check = ServerCheckSchema.model_construct(
        players={player_schema: snapshot_schema},
    )

    server = (await get_next_server_group(db))[0]
    handle_players(db, server, check)

    await db.commit()

    player_uuid = player.uuid

    db.expire_all()

    player = await db.scalar(  # type: ignore
        select(PlayerModel)
        .where(PlayerModel.uuid == player_uuid)
        .options(selectinload(PlayerModel.sessions))
    )

    assert player is not None
    assert len(player.sessions) == 2


async def test_handle_players_player_already_online(
    db: AsyncSession,
) -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25565,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
    )

    player = PlayerModel(
        uuid="11111111-1111-1111-1111-111111111111",
        player_type=PlayerType.PREMIUM,
    )

    snapshot = PlayerSnapshotModel(
        player=player,
        name="Steve",
        skin="skin1",
        cape="cape1",
    )

    session = PlayerSessionModel(
        player=player,
        server=server,
        from_=datetime(2000, 1, 1),
        to=None,
    )

    db.add_all([server, player, snapshot, session])
    await db.commit()

    player_schema = PlayerSchema(
        uuid=player.uuid,
        player_type=PlayerType.PREMIUM,
    )

    snapshot_schema = PlayerSnapshotSchema(
        name="Steve",
        skin="skin1",
        cape="cape1",
    )

    check = ServerCheckSchema.model_construct(
        players={player_schema: snapshot_schema},
    )

    server = (await get_next_server_group(db))[0]
    handle_players(db, server, check)

    player_uuid = player.uuid

    await db.commit()
    db.expire_all()

    player = await db.scalar(  # type: ignore
        select(PlayerModel)
        .where(PlayerModel.uuid == player_uuid)
        .options(selectinload(PlayerModel.sessions))
    )

    assert player is not None
    assert len(player.sessions) == 1


# == Tests for "handle_server_snapshot" ==


async def test_handle_server_snapshot_create_new_snapshot(
    db: AsyncSession,
) -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25565,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
    )

    db.add(server)
    await db.commit()

    check = ServerCheckSchema.model_construct(
        server=ServerSchema(
            ip="1.1.1.1",
            port=25565,
            server_type=ServerType.JAVA,
            is_lan=False,
            is_multiport=False,
        ),
        server_snapshot=ServerSnapshotSchema(
            version="1.20",
            players_max=100,
            motd="test",
            latency=50.0,
        ),
        server_dynamic_snapshot=ServerDynamicSnapshotSchema(
            players_online=10,
        ),
        software=SoftwareSchema(name=ServerSoftwareType.PAPER, version="1.20"),
        plugins=[],
        mods=[],
        players={},
    )

    server = (await get_next_server_group(db))[0]

    software_map = {}  # type: ignore
    plugin_map = {}  # type: ignore
    mod_map = {}  # type: ignore

    handle_server_snapshot(
        db,
        server,
        check,
        software_map,
        plugin_map,
        mod_map,
    )

    await db.commit()
    server_id = server.id

    db.expire_all()

    snapshot = await db.scalar(
        select(ServerSnapshotModel)
        .where(ServerSnapshotModel.server_id == server_id)
        .options(
            selectinload(ServerSnapshotModel.software),
            selectinload(ServerSnapshotModel.plugin_associations),
            selectinload(ServerSnapshotModel.mod_associations),
        )
    )

    assert snapshot is not None
    assert snapshot.software is not None
    assert snapshot.software.name == ServerSoftwareType.PAPER


async def test_handle_server_snapshot_software_change(
    db: AsyncSession,
) -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25565,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
    )
    software = SoftwareModel(name=ServerSoftwareType.PAPER, version="1.20")
    snapshot = ServerSnapshotModel(
        server=server,
        software=software,
        version="1.20",
        players_max=20,
        motd="test",
        latency=1,
    )

    db.add_all([server, software, snapshot])
    await db.commit()

    check = ServerCheckSchema.model_construct(
        server=ServerSchema(
            ip="1.1.1.1",
            port=25565,
            server_type=ServerType.JAVA,
            is_lan=False,
            is_multiport=False,
        ),
        server_snapshot=ServerSnapshotSchema(
            version="1.20",
            players_max=100,
            motd="test",
            latency=1,
        ),
        software=SoftwareSchema(name=ServerSoftwareType.FORGE, version="1.20"),
        plugins=[],
        mods=[],
    )

    server = (await get_next_server_group(db))[0]
    all_softwares, all_plugins, all_mods = extract_assets_from_servers(
        [(server, check)]
    )
    software_map = await load_existing_softwares(db, all_softwares)
    plugin_map = await load_existing_plugins(db, all_plugins)
    mod_map = await load_existing_mods(db, all_mods)

    handle_server_snapshot(
        db,
        server,
        check,
        software_map,
        plugin_map,
        mod_map,
    )

    await db.commit()
    server_id = server.id

    db.expire_all()

    snapshots = (
        (
            await db.execute(
                select(ServerSnapshotModel)
                .where(ServerSnapshotModel.server_id == server_id)
                .options(selectinload(ServerSnapshotModel.software))
            )
        )
        .scalars()
        .all()
    )

    assert len(snapshots) == 2

    software = (
        await db.execute(
            select(SoftwareModel).where(
                SoftwareModel.name == ServerSoftwareType.FORGE
            )
        )
    ).scalar_one_or_none()  # type: ignore

    assert software is not None


async def test_handle_server_snapshot_plugins_change(
    db: AsyncSession,
) -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25565,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
    )

    plugin_old = PluginModel(name="Essentials")
    snapshot = ServerSnapshotModel(
        server=server,
        version="1.20",
        players_max=20,
        motd="test",
        latency=1,
    )
    snapshot.plugin_associations.append(
        ServerSnapshotPluginAssociationModel(plugin=plugin_old)
    )

    db.add_all([server, plugin_old, snapshot])
    await db.commit()

    check = ServerCheckSchema.model_construct(
        server=ServerSchema(
            ip="1.1.1.1",
            port=25565,
            server_type=ServerType.JAVA,
            is_lan=False,
            is_multiport=False,
        ),
        server_snapshot=ServerSnapshotSchema(
            version="1.20",
            players_max=100,
            motd="test",
            latency=1,
        ),
        software=SoftwareSchema(name=ServerSoftwareType.PAPER, version="1.20"),
        plugins=[PluginSchema(name="LuckPerms")],
        mods=[],
    )

    server = (await get_next_server_group(db))[0]

    all_softwares, all_plugins, all_mods = extract_assets_from_servers(
        [(server, check)]
    )

    software_map = await load_existing_softwares(db, all_softwares)
    plugin_map = await load_existing_plugins(db, all_plugins)
    mod_map = await load_existing_mods(db, all_mods)

    handle_server_snapshot(
        db, server, check, software_map, plugin_map, mod_map
    )

    await db.commit()
    server_id = server.id
    db.expire_all()

    snapshots = (
        await db.scalars(
            select(ServerSnapshotModel)
            .where(ServerSnapshotModel.server_id == server_id)
            .options(
                selectinload(
                    ServerSnapshotModel.plugin_associations
                ).selectinload(ServerSnapshotPluginAssociationModel.plugin)
            )
        )
    ).all()

    assert len(snapshots) == 2

    new_snapshot = snapshots[1]
    plugin_names = {p.plugin.name for p in new_snapshot.plugin_associations}

    assert plugin_names == {"LuckPerms"}


async def test_handle_server_snapshot_mods_change(
    db: AsyncSession,
) -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25565,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
    )

    mod_old = ModModel(name="OldMod", version="1.0")

    snapshot = ServerSnapshotModel(
        server=server,
        version="1.20",
        players_max=20,
        motd="test",
        latency=1,
    )
    snapshot.mod_associations.append(
        ServerSnapshotModAssociationModel(mod=mod_old)
    )

    db.add_all([server, mod_old, snapshot])
    await db.commit()

    check = ServerCheckSchema.model_construct(
        server=ServerSchema(
            ip="1.1.1.1",
            port=25565,
            server_type=ServerType.JAVA,
            is_lan=False,
            is_multiport=False,
        ),
        server_snapshot=ServerSnapshotSchema(
            version="1.20",
            players_max=100,
            motd="test",
            latency=1,
        ),
        software=SoftwareSchema(name=ServerSoftwareType.PAPER, version="1.20"),
        plugins=[],
        mods=[ModSchema(name="NewMod", version="2.0")],
    )

    server = (await get_next_server_group(db))[0]

    all_softwares, all_plugins, all_mods = extract_assets_from_servers(
        [(server, check)]
    )

    software_map = await load_existing_softwares(db, all_softwares)
    plugin_map = await load_existing_plugins(db, all_plugins)
    mod_map = await load_existing_mods(db, all_mods)

    handle_server_snapshot(
        db, server, check, software_map, plugin_map, mod_map
    )

    await db.commit()
    server_id = server.id
    db.expire_all()

    snapshots = (
        await db.scalars(
            select(ServerSnapshotModel)
            .where(ServerSnapshotModel.server_id == server_id)
            .options(
                selectinload(
                    ServerSnapshotModel.mod_associations
                ).selectinload(ServerSnapshotModAssociationModel.mod)
            )
        )
    ).all()

    assert len(snapshots) == 2

    new_snapshot = snapshots[1]
    mod_names = {m.mod.name for m in new_snapshot.mod_associations}

    assert mod_names == {"NewMod"}
