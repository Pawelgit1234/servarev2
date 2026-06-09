from datetime import UTC, datetime

import pytest
from common.enums import PlayerType, ServerType
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
from monitor.services import get_next_server_group
from sqlalchemy.ext.asyncio import AsyncSession


# == Tests for "get_next_server_group" ==
@pytest.mark.asyncio
async def test_get_next_server_group_servers_with_same_ip(
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
async def test_get_next_server_group_loads_only_latest_snapshots(
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
async def test_get_next_server_group_loads_only_latest_dynamic_snapshots(
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


async def test_get_next_server_group_loads_only_latest_server_session(
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


async def test_get_next_server_group_loads_players(
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


# == Tests for "save_servers" ==
