from datetime import datetime

from common.enums import ServerType
from common.schemas.assets import ModSchema, PluginSchema, SoftwareSchema
from common.schemas.mixins import LastSeenMixin, TimestampMixin
from common.schemas.player import PlayerSchema, PlayerSnapshotSchema
from pydantic import BaseModel


class ServerSchema(TimestampMixin, LastSeenMixin):  # type: ignore
    ip: str
    port: int
    server_type: ServerType


class ServerSessionSchema(BaseModel):
    from_: datetime
    to: datetime | None = None


class ServerSnapshotSchema(TimestampMixin):  # type: ignore
    version: str
    players_max: int
    motd: str
    latency: float

    protocol: int | None = None
    favicon: str | None = None
    enforcesSecureChat: bool | None = None

    fml_network_version: int | None = None
    mods_truncated: bool | None = None

    map_name: str | None = None
    gamemode: str | None = None


class ServerDynamicSnapshotSchema(TimestampMixin):  # type: ignore
    players_online: int


class ServerBotSnapshotSchema(TimestampMixin):  # type: ignore
    pass


class ChunkSectionSchema(TimestampMixin):  # type: ignore
    hash: str


class ServerCheckSchema(BaseModel):
    server: ServerSchema
    server_snapshot: ServerSnapshotSchema
    server_dynamic_snapshot: ServerDynamicSnapshotSchema

    players: dict[PlayerSchema, PlayerSnapshotSchema]

    software: SoftwareSchema
    mods: list[ModSchema]
    plugins: list[PluginSchema]
