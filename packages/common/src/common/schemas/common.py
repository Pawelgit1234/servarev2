from dataclasses import dataclass

from common.enums import AssetField
from common.models.assets import ModModel, PluginModel, SoftwareModel
from common.models.player import PlayerModel
from common.schemas.assets import ModSchema, PluginSchema, SoftwareSchema
from common.schemas.player import PlayerSchema, PlayerSnapshotSchema
from common.schemas.server import ServerSnapshotSchema


@dataclass(slots=True)
class PendingServerAssetSchema:
    owner: ServerSnapshotSchema | PlayerSnapshotSchema
    field: AssetField
    source: str
    is_base64: bool
    prefix: str
    content_type: str | None = None
    data: bytes | None = None


@dataclass(slots=True)
class ExistingEntityMapsSchema:
    software_map: dict[SoftwareSchema, SoftwareModel]
    plugin_map: dict[PluginSchema, PluginModel]
    mod_map: dict[ModSchema, ModModel]
    player_map: dict[PlayerSchema, PlayerModel]


@dataclass(slots=True)
class ExtractedEntitiesSchema:
    softwares: list[SoftwareSchema]
    plugins: list[PluginSchema]
    mods: list[ModSchema]
    players: list[PlayerSchema]
