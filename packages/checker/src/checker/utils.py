from common.schemas.assets import ModSchema, PluginSchema, SoftwareSchema
from common.schemas.common import ExtractedEntitiesSchema
from common.schemas.player import PlayerSchema
from common.schemas.server import ServerCheckSchema


def extract_entities_from_checks(
    checks: list[ServerCheckSchema],
) -> ExtractedEntitiesSchema:
    softwares: list[SoftwareSchema] = []
    plugins: list[PluginSchema] = []
    mods: list[ModSchema] = []
    players: list[PlayerSchema] = []

    for check in checks:
        softwares.append(check.software)
        plugins.extend(check.plugins)
        mods.extend(check.mods)
        players.extend(check.players.keys())

    return ExtractedEntitiesSchema(
        softwares=softwares,
        plugins=plugins,
        mods=mods,
        players=players,
    )
