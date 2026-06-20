from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

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
from common.schemas.ip import IpInfoSchema
from common.settings import REDIS_PORTER_QUEUE
from monitor.services import get_next_server_group, prepare_ip_data
from sqlalchemy.ext.asyncio import AsyncSession


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


# == Tests for "prepare_ip_data" ==
@pytest.mark.asyncio
async def test_prepare_ip_data_both_expired_calls_ip_and_redis() -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25566,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
        last_ip_check_at=datetime(2000, 1, 1, 1, 1, 1),
        last_porter_check_at=datetime(2000, 1, 1, 1, 1, 1),
    )

    fake_ip = IpInfoSchema(
        country="DE",
        region="Berlin",
        city="Berlin",
        latitude=51.0,
        longitude=7.0,
        hostname="host",
        asn="ASN 123",
    )

    with patch("monitor.services.ra.rpush", new=AsyncMock()) as rpush_mock:  # noqa: SIM117
        with patch(
            "monitor.services.get_ip_info", new=AsyncMock(return_value=fake_ip)
        ) as ip_mock:
            ip_info, update_porter = await prepare_ip_data(server)

    rpush_mock.assert_awaited_once_with(REDIS_PORTER_QUEUE, server.ip)

    assert ip_info == fake_ip
    assert update_porter is True
    ip_mock.assert_awaited_once_with("1.1.1.1")


@pytest.mark.asyncio
async def test_prepare_ip_data_only_ip_expired_calls_ip_only() -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25566,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
        last_ip_check_at=datetime(2000, 1, 1, 1, 1, 1),
        last_porter_check_at=datetime(3000, 1, 1, 1, 1, 1),  # not expired
    )

    fake_ip = IpInfoSchema(
        country="DE",
        region="Berlin",
        city="Berlin",
        latitude=51.0,
        longitude=7.0,
        hostname="host",
        asn="ASN 123",
    )

    with patch(  # noqa: SIM117
        "monitor.services.get_ip_info", new=AsyncMock(return_value=fake_ip)
    ) as ip_mock:
        with patch("monitor.services.ra.rpush", new=AsyncMock()) as rpush_mock:
            ip_info, update_porter = await prepare_ip_data(server)

    assert ip_info == fake_ip
    assert update_porter is False

    ip_mock.assert_awaited_once_with("1.1.1.1")
    rpush_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_prepare_ip_data_only_porter_expired_calls_redis_only() -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25566,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
        last_ip_check_at=datetime(3000, 1, 1, 1, 1, 1),  # not expired
        last_porter_check_at=datetime(2000, 1, 1, 1, 1, 1),
    )

    with patch("monitor.services.get_ip_info", new=AsyncMock()) as ip_mock:  # noqa: SIM117
        with patch("monitor.services.ra.rpush", new=AsyncMock()) as rpush_mock:
            ip_info, update_porter = await prepare_ip_data(server)

    assert ip_info is None
    assert update_porter is True

    ip_mock.assert_not_awaited()
    rpush_mock.assert_awaited_once_with(
        REDIS_PORTER_QUEUE,
        server.ip,
    )


@pytest.mark.asyncio
async def test_prepare_ip_data_none_expired_calls_nothing() -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25566,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
        last_ip_check_at=datetime(3000, 1, 1, 1, 1, 1),
        last_porter_check_at=datetime(3000, 1, 1, 1, 1, 1),
    )

    with patch("monitor.services.get_ip_info", new=AsyncMock()) as ip_mock:  # noqa: SIM117
        with patch("monitor.services.ra.rpush", new=AsyncMock()) as rpush_mock:
            ip_info, update_porter = await prepare_ip_data(server)

    assert ip_info is None
    assert update_porter is False

    ip_mock.assert_not_awaited()
    rpush_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_prepare_ip_data_multiport_skips_porter() -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25566,
        is_lan=False,
        is_multiport=True,
        server_type=ServerType.JAVA,
        last_ip_check_at=datetime(3000, 1, 1, 1, 1, 1),
        last_porter_check_at=datetime(2000, 1, 1, 1, 1, 1),
    )

    with patch("monitor.services.get_ip_info", new=AsyncMock()) as ip_mock:  # noqa: SIM117
        with patch("monitor.services.ra.rpush", new=AsyncMock()) as rpush_mock:
            ip_info, update_porter = await prepare_ip_data(server)

    assert ip_info is None
    assert update_porter is False

    ip_mock.assert_not_awaited()
    rpush_mock.assert_not_awaited()
