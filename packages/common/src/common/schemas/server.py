from datetime import UTC, datetime

from common.enums import DetectedServiceType, ProtocolType, ServerType
from common.schemas.assets import ModSchema, PluginSchema, SoftwareSchema
from common.schemas.ip import IpInfoSchema
from common.schemas.mixins import LastSeenMixin, TimestampMixin
from common.schemas.player import PlayerSchema, PlayerSnapshotSchema
from pydantic import BaseModel, ConfigDict, Field


class IpSchema(IpInfoSchema, LastSeenMixin):  # type: ignore
    ip: str
    is_multiport: bool = False
    last_ip_check_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )
    last_porter_check_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )


class ServerSchema(TimestampMixin):  # type: ignore
    port: int
    server_type: ServerType
    is_lan: bool = False


class IpPortSchema(BaseModel):  # type: ignore
    model_config = ConfigDict(frozen=True)

    port: int
    protocol_type: ProtocolType
    detected_service_type: DetectedServiceType


class ServerSessionSchema(BaseModel):  # type: ignore
    from_: datetime
    to: datetime | None = None


class ServerSnapshotSchema(TimestampMixin):  # type: ignore
    version: str
    players_max: int
    motd: str
    latency: float

    protocol: int | None = None
    icon: str | None = None
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


class ServerCheckSchema(BaseModel):  # type: ignore
    server: ServerSchema
    server_snapshot: ServerSnapshotSchema
    server_dynamic_snapshot: ServerDynamicSnapshotSchema

    players: dict[PlayerSchema, PlayerSnapshotSchema]

    software: SoftwareSchema
    mods: list[ModSchema]
    plugins: list[PluginSchema]
