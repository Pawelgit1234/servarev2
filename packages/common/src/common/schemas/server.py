from typing import Any

from common.enums import ServerType
from pydantic import BaseModel, ConfigDict


class ServerSchema(BaseModel):
    port: int
    ip: str
    server_type: ServerType


class ServerSnapshotSchema(BaseModel):
    is_online: bool = True
    version: str
    players_max: int
    motd: str
    latency: float
    raw: dict[str, Any]

    protocol: int | None = None
    favicon: str | None = None
    enforcesSecureChat: bool | None = None

    fml_network_version: int | None = None
    mods_truncated: bool | None = None

    map_name: str | None = None
    gamemode: str | None = None

    model_config = ConfigDict(from_attributes=True)
