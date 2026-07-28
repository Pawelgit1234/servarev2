from common.schemas.common import (
    ExistingEntityMapsSchema,
    ExtractedEntitiesSchema,
)
from common.services.assets import (
    load_existing_mods,
    load_existing_plugins,
    load_existing_softwares,
)
from common.services.player import load_existing_players
from sqlalchemy.ext.asyncio import AsyncSession


async def load_existing_entities(
    db: AsyncSession, ee: ExtractedEntitiesSchema
) -> ExistingEntityMapsSchema:
    return ExistingEntityMapsSchema(
        software_map=await load_existing_softwares(db, ee.softwares),
        plugin_map=await load_existing_plugins(db, ee.plugins),
        mod_map=await load_existing_mods(db, ee.mods),
        player_map=await load_existing_players(db, ee.players),
    )
