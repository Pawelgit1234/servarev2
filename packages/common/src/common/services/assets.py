from common.models.assets import ModModel, PluginModel, SoftwareModel
from common.schemas.assets import ModSchema, PluginSchema, SoftwareSchema
from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession


async def load_existing_softwares(
    db: AsyncSession, softwares: list[SoftwareSchema]
) -> dict[SoftwareSchema, SoftwareModel]:
    keys = {(s.name, s.version) for s in softwares}

    rows = (
        (
            await db.execute(
                select(SoftwareModel).where(
                    tuple_(
                        SoftwareModel.name,
                        SoftwareModel.version,
                    ).in_(keys)
                )
            )
        )
        .scalars()
        .all()
    )

    rows_map = {(s.name, s.version): s for s in rows}

    return {
        software: rows_map[(software.name, software.version)]
        for software in softwares
        if (software.name, software.version) in rows_map
    }


async def load_existing_plugins(
    db: AsyncSession, plugins: list[PluginSchema]
) -> dict[PluginSchema, PluginModel]:
    names = {p.name for p in plugins}

    rows = (
        (
            await db.execute(
                select(PluginModel).where(PluginModel.name.in_(names))
            )
        )
        .scalars()
        .all()
    )

    rows_map = {p.name: p for p in rows}

    return {
        plugin: rows_map[plugin.name]
        for plugin in plugins
        if plugin.name in rows_map
    }


async def load_existing_mods(
    db: AsyncSession, mods: list[ModSchema]
) -> dict[ModSchema, ModModel]:
    mod_keys = {(m.name, m.version) for m in mods}

    rows = (
        (
            await db.execute(
                select(ModModel).where(
                    tuple_(ModModel.name, ModModel.version).in_(mod_keys)
                )
            )
        )
        .scalars()
        .all()
    )

    rows_map = {(m.name, m.version): m for m in rows}

    return {
        mod_schema: rows_map[(mod_schema.name, mod_schema.version)]
        for mod_schema in mods
        if (mod_schema.name, mod_schema.version) in rows_map
    }
