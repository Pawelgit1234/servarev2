import base64

from common.enums import PlayerType, ServerSoftwareType, ServerType
from common.schemas.assets import ModSchema, PluginSchema, SoftwareSchema
from common.schemas.player import PlayerSchema, PlayerSnapshotSchema
from common.schemas.server import (
    ServerCheckSchema,
    ServerDynamicSnapshotSchema,
    ServerSchema,
    ServerSnapshotSchema,
)
from common.settings import (
    ASN_MAX,
    CITY_MAX,
    COUNTRY_MAX,
    HOSTNAME_MAX,
    MOD_NAME_MAX,
    MOD_VERSION_MAX,
    PLUGIN_NAME_MAX,
    REGION_MAX,
    SERVER_GAMEMODE_MAX,
    SERVER_MAP_NAME_MAX,
    SERVER_MOTD_MAX,
    SERVER_VERSION_MAX,
    SOFTWARE_VESION_MAX,
    USERNAME_MAX,
)
from common.utils import (
    decode_base64,
    normilize_server_check,
)


def create_server_check() -> ServerCheckSchema:
    return ServerCheckSchema(
        server=ServerSchema(
            ip="127.0.0.1",
            port=25565,
            server_type=ServerType.JAVA,
            is_lan=False,
            is_multiport=False,
            country="X" * 100,
            region="X" * 1000,
            city="X" * 1000,
            hostname="X" * 1000,
            asn="X" * 1000,
        ),
        server_snapshot=ServerSnapshotSchema(
            version="X" * 1000,
            players_max=20,
            motd="X" * 5000,
            latency=1.0,
            map_name="X" * 1000,
            gamemode="X" * 1000,
        ),
        server_dynamic_snapshot=ServerDynamicSnapshotSchema(
            players_online=5,
        ),
        players={
            PlayerSchema(
                player_type=PlayerType.PREMIUM,
                uuid="uuid",
            ): PlayerSnapshotSchema(
                name="X" * 1000,
            )
        },
        software=SoftwareSchema(
            name=ServerSoftwareType.PAPER,
            version="X" * 1000,
        ),
        mods=[
            ModSchema(
                name="X" * 1000,
                version="X" * 1000,
            )
        ],
        plugins=[
            PluginSchema(
                name="X" * 1000,
            )
        ],
    )


def test_decode_base64() -> None:
    data = b"hello"
    encoded = base64.b64encode(data).decode()
    assert decode_base64(encoded) == data


def test_decode_base64_data_url() -> None:
    data = b"hello"

    encoded = "data:image/png;base64," + base64.b64encode(data).decode()

    assert decode_base64(encoded) == data


def test_decode_base64_invalid() -> None:
    assert decode_base64("invalid base64") is None


def test_normilize_server_check() -> None:
    server = create_server_check()

    normilize_server_check(server)

    assert len(server.server.country) == COUNTRY_MAX  # type: ignore
    assert len(server.server.region) == REGION_MAX  # type: ignore
    assert len(server.server.city) == CITY_MAX  # type: ignore
    assert len(server.server.hostname) == HOSTNAME_MAX  # type: ignore
    assert len(server.server.asn) == ASN_MAX  # type: ignore

    assert len(server.server_snapshot.version) == SERVER_VERSION_MAX

    assert len(server.server_snapshot.motd) == SERVER_MOTD_MAX

    assert (
        len(server.server_snapshot.map_name)  # type: ignore
        == SERVER_MAP_NAME_MAX
    )

    assert (
        len(server.server_snapshot.gamemode)  # type: ignore
        == SERVER_GAMEMODE_MAX
    )

    assert len(server.software.version) == SOFTWARE_VESION_MAX

    assert len(server.mods[0].name) == MOD_NAME_MAX

    assert len(server.mods[0].version) == MOD_VERSION_MAX

    assert len(server.plugins[0].name) == PLUGIN_NAME_MAX

    player_snapshot = next(iter(server.players.values()))

    assert len(player_snapshot.name) == USERNAME_MAX
