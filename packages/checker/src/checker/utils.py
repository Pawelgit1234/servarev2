from common.schemas.assets import ModSchema, PluginSchema, SoftwareSchema
from common.schemas.server import ServerCheckSchema


def extract_assets_from_checks(
    checks: list[ServerCheckSchema],
) -> tuple[list[SoftwareSchema], list[PluginSchema], list[ModSchema]]:
    all_softwares = []
    all_plugins = []
    all_mods = []

    for check in checks:
        all_softwares.append(check.software)
        all_plugins.extend(check.plugins)
        all_mods.extend(check.mods)

    return all_softwares, all_plugins, all_mods
