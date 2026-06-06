import pytest
from common.enums import ServerType
from common.models.server import (
    ServerModel,
    ServerSnapshotModel,
)
from monitor.services import get_next_server_group
from sqlalchemy.ext.asyncio import AsyncSession


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
    )

    new_snapshot = ServerSnapshotModel(
        server=server,
        version="1.20",
        players_max=100,
        motd="new",
        latency=1,
    )

    db.add_all([old_snapshot, new_snapshot])
    await db.commit()

    servers = await get_next_server_group(db)

    assert len(servers) == 1

    loaded_server = servers[0]

    assert len(loaded_server.snapshots) == 1
    assert loaded_server.snapshots[0].version == "1.20"


# @pytest.mark.asyncio
# async def test_get_next_server_group_loads_only_latest_dynamic_snapshot(
#     db: AsyncSession,
# ) -> None:
#     server = ServerModel(
#         ip="2.2.2.2",
#         port=25565,
#         is_lan=False,
#         is_multiport=False,
#         server_type=ServerType.JAVA,
#     )
#     db.add(server)
#     await db.flush()
#
#     old_dynamic = ServerDynamicSnapshotModel(
#         server=server,
#         players_online=5,
#     )
#
#     new_dynamic = ServerDynamicSnapshotModel(
#         server=server,
#         players_online=50,
#     )
#
#     db.add_all([old_dynamic, new_dynamic])
#     await db.commit()
#
#     servers = await get_next_server_group(db)
#
#     loaded_server = servers[0]
#
#     assert len(loaded_server.dynamic_snapshots) == 1
#     assert loaded_server.dynamic_snapshots[0].players_online == 50
#
#
# @pytest.mark.asyncio
# async def test_get_next_server_group_loads_only_latest_server_session(
#     db: AsyncSession,
# ) -> None:
#     server = ServerModel(
#         ip="3.3.3.3",
#         port=25565,
#         is_lan=False,
#         is_multiport=False,
#         server_type=ServerType.JAVA,
#     )
#     db.add(server)
#     await db.flush()
#
#     old_session = ServerSessionModel(server=server)
#     new_session = ServerSessionModel(server=server)
#
#     db.add_all([old_session, new_session])
#     await db.commit()
#
#     servers = await get_next_server_group(db)
#
#     loaded_server = servers[0]
#
#     assert len(loaded_server.sessions) == 1
#     assert loaded_server.sessions[0].id == new_session.id
#
#
# @pytest.mark.asyncio
# async def test_get_next_server_group_loads_latest_player_session_per_uuid(
#     db: AsyncSession,
# ) -> None:
#     server = ServerModel(
#         ip="4.4.4.4",
#         port=25565,
#         is_lan=False,
#         is_multiport=False,
#         server_type=ServerType.JAVA,
#     )
#     db.add(server)
#     await db.flush()
#
#     player_old = PlayerModel(
#         uuid="same-uuid",
#         player_type=PlayerType.PREMIUM,
#     )
#
#     player_new = PlayerModel(
#         uuid="same-uuid",
#         player_type=PlayerType.PREMIUM,
#     )
#
#     db.add_all([player_old, player_new])
#     await db.flush()
#
#     old_session = PlayerSessionModel(
#         player=player_old,
#         server=server,
#     )
#
#     new_session = PlayerSessionModel(
#         player=player_new,
#         server=server,
#     )
#
#     db.add_all([old_session, new_session])
#     await db.commit()
#
#     servers = await get_next_server_group(db)
#
#     loaded_server = servers[0]
#
#     assert len(loaded_server.player_sessions) == 1
#     assert loaded_server.player_sessions[0].player.uuid == "same-uuid"
#     assert loaded_server.player_sessions[0].id == new_session.id
#
#
# @pytest.mark.asyncio
# async def test_get_next_server_group_loads_snapshot_assets(
#     db: AsyncSession,
# ) -> None:
#     server = ServerModel(
#         ip="5.5.5.5",
#         port=25565,
#         is_lan=False,
#         is_multiport=False,
#         server_type=ServerType.JAVA,
#     )
#
#     software = SoftwareModel(
#         name=ServerSoftwareType.PAPER,
#         version="1.20",
#     )
#
#     plugin = PluginModel(
#         name="WorldEdit",
#     )
#
#     mod = ModModel(
#         name="FabricAPI",
#         version="0.1",
#     )
#
#     snapshot = ServerSnapshotModel(
#         server=server,
#         version="1.20",
#         players_max=100,
#         motd="test",
#         latency=1,
#         software=software,
#     )
#
#     snapshot.plugin_associations.append(
#         ServerSnapshotPluginAssociationModel(
#             plugin=plugin,
#         )
#     )
#
#     snapshot.mod_associations.append(
#         ServerSnapshotModAssociationModel(
#             mod=mod,
#         )
#     )
#
#     db.add(server)
#     await db.commit()
#
#     servers = await get_next_server_group(db)
#
#     loaded_snapshot = servers[0].snapshots[0]
#
#     assert loaded_snapshot.software is not None
#     assert loaded_snapshot.software.name == ServerSoftwareType.PAPER
#
#     assert len(loaded_snapshot.plugin_associations) == 1
#     assert loaded_snapshot.plugin_associations[0].plugin.name == "WorldEdit"
#
#     assert len(loaded_snapshot.mod_associations) == 1
#     assert loaded_snapshot.mod_associations[0].mod.name == "FabricAPI"
