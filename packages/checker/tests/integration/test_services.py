from checker.services import save_non_existing_servers, save_ports
from common.enums import (
    DetectedServiceType,
    PlayerType,
    ProtocolType,
    ServerSoftwareType,
    ServerType,
)
from common.models.assets import (
    ModModel,
    PluginModel,
    ServerSnapshotModAssociationModel,
    ServerSnapshotPluginAssociationModel,
    SoftwareModel,
)
from common.models.player import PlayerModel
from common.models.server import (
    IpPortModel,
    ServerModel,
    ServerPortAssociationModel,
    ServerSnapshotModel,
)
from common.schemas.assets import ModSchema, PluginSchema, SoftwareSchema
from common.schemas.player import PlayerSchema, PlayerSnapshotSchema
from common.schemas.server import (
    IpPortSchema,
    ServerCheckSchema,
    ServerDynamicSnapshotSchema,
    ServerSchema,
    ServerSnapshotSchema,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


# == Tests for "save_non_existing_servers" ==
async def test_save_non_existing_servers(
    db: AsyncSession,
) -> None:
    check1 = ServerCheckSchema(
        server=ServerSchema(
            ip="1.1.1.1",
            port=25565,
            server_type=ServerType.JAVA,
            is_lan=False,
            is_multiport=False,
            country="US",
            region="Region1",
            city="City1",
            latitude=1.0,
            longitude=2.0,
            hostname="host1",
            asn="123",
        ),
        server_snapshot=ServerSnapshotSchema(
            version="1.20.1",
            players_max=20,
            motd="Server 1",
            latency=10,
            protocol=763,
            icon="icon1",
            enforcesSecureChat=True,
            fml_network_version=1,
            mods_truncated=False,
            map_name="world",
            gamemode="survival",
        ),
        server_dynamic_snapshot=ServerDynamicSnapshotSchema(
            players_online=1,
        ),
        players={
            PlayerSchema(
                uuid="11111111-1111-1111-1111-111111111111",
                player_type=PlayerType.PREMIUM,
            ): PlayerSnapshotSchema(
                name="Steve",
                skin="skin1",
                cape="cape1",
            )
        },
        software=SoftwareSchema(
            name=ServerSoftwareType.PAPER,
            version="1.20.1",
        ),
        plugins=[
            PluginSchema(name="Essentials"),
        ],
        mods=[
            ModSchema(name="FabricAPI", version="0.1"),
        ],
    )

    check2 = ServerCheckSchema(
        server=ServerSchema(
            ip="2.2.2.2",
            port=25566,
            server_type=ServerType.JAVA,
            is_lan=True,
            is_multiport=True,
            country="RU",
            region="Region2",
            city="City2",
            latitude=3.0,
            longitude=4.0,
            hostname="host2",
            asn="456",
        ),
        server_snapshot=ServerSnapshotSchema(
            version="1.21",
            players_max=100,
            motd="Server 2",
            latency=20,
            protocol=800,
            icon="icon2",
            enforcesSecureChat=False,
            fml_network_version=2,
            mods_truncated=True,
            map_name="nether",
            gamemode="creative",
        ),
        server_dynamic_snapshot=ServerDynamicSnapshotSchema(
            players_online=2,
        ),
        players={
            PlayerSchema(
                uuid="22222222-2222-2222-2222-222222222222",
                player_type=PlayerType.PREMIUM,
            ): PlayerSnapshotSchema(
                name="Alex",
                skin="skin2",
                cape="cape2",
            )
        },
        software=SoftwareSchema(
            name=ServerSoftwareType.PURPUR,
            version="1.21",
        ),
        plugins=[
            PluginSchema(name="LuckPerms"),
        ],
        mods=[
            ModSchema(name="WorldEdit", version="7.3"),
        ],
    )

    servers = await save_non_existing_servers(db, [check1, check2])
    await db.commit()

    assert len(servers) == 2

    db.expire_all()

    saved_servers = (
        (
            await db.execute(
                select(ServerModel).options(
                    selectinload(ServerModel.snapshots).selectinload(
                        ServerSnapshotModel.software
                    ),
                    selectinload(ServerModel.snapshots)
                    .selectinload(ServerSnapshotModel.plugin_associations)
                    .selectinload(ServerSnapshotPluginAssociationModel.plugin),
                    selectinload(ServerModel.snapshots)
                    .selectinload(ServerSnapshotModel.mod_associations)
                    .selectinload(ServerSnapshotModAssociationModel.mod),
                    selectinload(ServerModel.dynamic_snapshots),
                    selectinload(ServerModel.sessions),
                )
            )
        )
        .scalars()
        .all()
    )

    assert len(saved_servers) == 2

    server1 = next(s for s in saved_servers if s.ip == "1.1.1.1")
    server2 = next(s for s in saved_servers if s.ip == "2.2.2.2")

    assert server1.country == "US"
    assert server2.country == "RU"

    assert len(server1.sessions) == 1
    assert len(server2.sessions) == 1

    assert len(server1.dynamic_snapshots) == 1
    assert len(server2.dynamic_snapshots) == 1

    assert len(server1.snapshots) == 1
    assert len(server2.snapshots) == 1

    snapshot1 = server1.snapshots[0]
    snapshot2 = server2.snapshots[0]

    assert snapshot1.software.name == ServerSoftwareType.PAPER
    assert snapshot2.software.name == ServerSoftwareType.PURPUR

    assert {a.plugin.name for a in snapshot1.plugin_associations} == {
        "Essentials"
    }
    assert {a.plugin.name for a in snapshot2.plugin_associations} == {
        "LuckPerms"
    }

    assert {a.mod.name for a in snapshot1.mod_associations} == {"FabricAPI"}
    assert {a.mod.name for a in snapshot2.mod_associations} == {"WorldEdit"}

    players = (await db.execute(select(PlayerModel))).scalars().all()
    assert len(players) == 2


async def test_save_non_existing_servers_reuses_existing_assets(
    db: AsyncSession,
) -> None:
    existing_software = SoftwareModel(
        name=ServerSoftwareType.PAPER,
        version="1.20.1",
    )
    existing_plugin = PluginModel(name="Essentials")
    existing_mod = ModModel(
        name="FabricAPI",
        version="0.1",
    )

    db.add_all([existing_software, existing_plugin, existing_mod])
    await db.commit()

    check = ServerCheckSchema(
        server=ServerSchema(
            ip="1.1.1.1",
            port=25565,
            server_type=ServerType.JAVA,
            is_lan=False,
            is_multiport=False,
            country="US",
            region="Region",
            city="City",
            latitude=1.0,
            longitude=2.0,
            hostname="host",
            asn="123",
        ),
        server_snapshot=ServerSnapshotSchema(
            version="1.20.1",
            players_max=20,
            motd="Test",
            latency=10,
            protocol=763,
            icon="icon",
            enforcesSecureChat=True,
            fml_network_version=1,
            mods_truncated=False,
            map_name="world",
            gamemode="survival",
        ),
        server_dynamic_snapshot=ServerDynamicSnapshotSchema(
            players_online=1,
        ),
        players={
            PlayerSchema(
                uuid="11111111-1111-1111-1111-111111111111",
                player_type=PlayerType.PREMIUM,
            ): PlayerSnapshotSchema(
                name="Steve",
                skin="skin",
                cape="cape",
            )
        },
        software=SoftwareSchema(
            name=ServerSoftwareType.PAPER,
            version="1.20.1",
        ),
        plugins=[
            PluginSchema(name="Essentials"),  # already exists
            PluginSchema(name="LuckPerms"),  # new
        ],
        mods=[
            ModSchema(name="FabricAPI", version="0.1"),  # already exists
            ModSchema(name="WorldEdit", version="7.3"),  # new
        ],
    )

    await save_non_existing_servers(db, [check])
    await db.commit()

    existing_software_id = existing_software.id
    existing_plugin_id = existing_plugin.id
    existing_mod_id = existing_mod.id

    db.expire_all()

    softwares = (await db.execute(select(SoftwareModel))).scalars().all()
    plugins = (await db.execute(select(PluginModel))).scalars().all()
    mods = (await db.execute(select(ModModel))).scalars().all()

    assert len(softwares) == 1
    assert len(plugins) == 2
    assert len(mods) == 2

    server = await db.scalar(
        select(ServerModel).options(
            selectinload(ServerModel.snapshots).selectinload(
                ServerSnapshotModel.software
            ),
            selectinload(ServerModel.snapshots)
            .selectinload(ServerSnapshotModel.plugin_associations)
            .selectinload(ServerSnapshotPluginAssociationModel.plugin),
            selectinload(ServerModel.snapshots)
            .selectinload(ServerSnapshotModel.mod_associations)
            .selectinload(ServerSnapshotModAssociationModel.mod),
        )
    )

    assert server is not None

    snapshot = server.snapshots[0]

    # software must be reused
    assert snapshot.software.id == existing_software_id

    plugin_names = {
        assoc.plugin.name for assoc in snapshot.plugin_associations
    }
    assert plugin_names == {"Essentials", "LuckPerms"}

    mod_names = {assoc.mod.name for assoc in snapshot.mod_associations}
    assert mod_names == {"FabricAPI", "WorldEdit"}

    # already existing assets must be reused
    essentials = await db.scalar(
        select(PluginModel).where(PluginModel.name == "Essentials")
    )
    fabric_api = await db.scalar(
        select(ModModel).where(
            ModModel.name == "FabricAPI",
            ModModel.version == "0.1",
        )
    )

    assert essentials is not None
    assert essentials.id == existing_plugin_id

    assert fabric_api is not None
    assert fabric_api.id == existing_mod_id


# == Tests for "save_ports" ==


async def test_save_ports_create_new_server_and_port(
    db: AsyncSession,
) -> None:
    port = IpPortSchema(
        port=80,
        protocol_type=ProtocolType.TCP,
        detected_service_type=DetectedServiceType.BLUEMAP,
    )

    check = ServerCheckSchema(
        server=ServerSchema(
            ip="1.1.1.1",
            port=25565,
            server_type=ServerType.JAVA,
            is_lan=False,
            is_multiport=False,
        ),
        server_snapshot=ServerSnapshotSchema(
            version="1.20", players_max=20, motd="test", latency=1
        ),
        server_dynamic_snapshot=ServerDynamicSnapshotSchema(players_online=0),
        players={},
        software=SoftwareSchema(name=ServerSoftwareType.PAPER, version="1.20"),
        plugins=[],
        mods=[],
    )

    await save_ports(db, [port], [check], "1.1.1.1")
    await db.commit()

    assert await db.scalar(select(func.count(ServerModel.id))) == 1
    assert await db.scalar(select(func.count(IpPortModel.id))) == 1
    assert (
        await db.scalar(
            select(func.count(ServerPortAssociationModel.server_id))
        )
        == 1
    )


async def test_save_ports_reuse_existing_server(
    db: AsyncSession,
) -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25565,
        server_type=ServerType.JAVA,
        is_lan=False,
        is_multiport=False,
    )

    db.add(server)
    await db.commit()

    port = IpPortSchema(
        port=80,
        protocol_type=ProtocolType.TCP,
        detected_service_type=DetectedServiceType.BLUEMAP,
    )

    check = ServerCheckSchema(
        server=ServerSchema(
            ip="1.1.1.1",
            port=25565,
            server_type=ServerType.JAVA,
            is_lan=False,
            is_multiport=False,
        ),
        server_snapshot=ServerSnapshotSchema(
            version="1.20",
            players_max=20,
            motd="test",
            latency=1,
        ),
        server_dynamic_snapshot=ServerDynamicSnapshotSchema(
            players_online=0,
        ),
        players={},
        software=SoftwareSchema(
            name=ServerSoftwareType.PAPER,
            version="1.20",
        ),
        plugins=[],
        mods=[],
    )

    await save_ports(db, [port], [check], "1.1.1.1")
    await db.commit()

    servers = (await db.execute(select(ServerModel))).scalars().all()
    assert len(servers) == 1

    assoc = await db.scalar(select(ServerPortAssociationModel))

    assert assoc is not None
    assert assoc.server_id == server.id


async def test_save_ports_reuse_existing_port_and_association(
    db: AsyncSession,
) -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25565,
        server_type=ServerType.JAVA,
        is_lan=False,
        is_multiport=False,
    )

    existing_port = IpPortModel(
        port=80,
        protocol_type=ProtocolType.TCP,
        detected_service_type=DetectedServiceType.BLUEMAP,
    )

    assoc = ServerPortAssociationModel(
        server=server,
        server_port=existing_port,
    )

    db.add_all([server, existing_port, assoc])
    await db.commit()

    ports = [
        IpPortSchema(
            port=80,
            protocol_type=ProtocolType.TCP,
            detected_service_type=DetectedServiceType.BLUEMAP,
        ),
        IpPortSchema(
            port=443,
            protocol_type=ProtocolType.TCP,
            detected_service_type=DetectedServiceType.PELICAN,
        ),
    ]

    check = ServerCheckSchema(
        server=ServerSchema(
            ip="1.1.1.1",
            port=25565,
            server_type=ServerType.JAVA,
            is_lan=False,
            is_multiport=False,
        ),
        server_snapshot=ServerSnapshotSchema(
            version="1.20",
            players_max=20,
            motd="test",
            latency=1,
        ),
        server_dynamic_snapshot=ServerDynamicSnapshotSchema(
            players_online=0,
        ),
        players={},
        software=SoftwareSchema(
            name=ServerSoftwareType.PAPER,
            version="1.20",
        ),
        plugins=[],
        mods=[],
    )

    await save_ports(db, ports, [check], "1.1.1.1")
    await db.commit()

    all_ports = (await db.execute(select(IpPortModel))).scalars().all()

    associations = (
        (await db.execute(select(ServerPortAssociationModel))).scalars().all()
    )

    assert len(all_ports) == 2
    assert len(associations) == 2

    existing = next(p for p in all_ports if p.port == 80)
    new = next(p for p in all_ports if p.port == 443)

    assert existing.id == existing_port.id
    assert new.id != existing_port.id
