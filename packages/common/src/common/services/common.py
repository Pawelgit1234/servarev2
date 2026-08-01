import asyncio
import logging
from collections.abc import Callable, Iterable
from typing import TypeVar

from common.checks.player import download_by_url
from common.enums import AssetField
from common.s3client import s3
from common.schemas.common import PendingServerAssetSchema
from common.schemas.player import PlayerSnapshotSchema
from common.schemas.server import ServerCheckSchema
from common.settings import S3_CAPE_PREFIX, S3_ICON_PREFIX, S3_SKIN_PREFIX
from common.utils import decode_base64
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

SchemaT = TypeVar("SchemaT")
ModelT = TypeVar("ModelT")


def ensure_entity[SchemaT, ModelT](
    db: AsyncSession,
    entity_map: dict[SchemaT, ModelT],
    schema: SchemaT,
    factory: Callable[[SchemaT], ModelT],
) -> ModelT:
    entity = entity_map.get(schema)

    if entity is None:
        entity = factory(schema)
        entity_map[schema] = entity
        db.add(entity)

    return entity


def collect_player_assets(
    player_snapshots: Iterable[PlayerSnapshotSchema],
) -> list[PendingServerAssetSchema]:
    assets = []
    for snapshot in player_snapshots:
        if snapshot.skin is not None:
            assets.append(
                PendingServerAssetSchema(
                    owner=snapshot,
                    field=AssetField.SKIN,
                    prefix=S3_SKIN_PREFIX,
                    source=snapshot.skin,
                    is_base64=False,
                )
            )

        if snapshot.cape is not None:
            assets.append(
                PendingServerAssetSchema(
                    owner=snapshot,
                    field=AssetField.CAPE,
                    prefix=S3_CAPE_PREFIX,
                    source=snapshot.cape,
                    is_base64=False,
                )
            )
    return assets


def collect_assets(
    servers: list[ServerCheckSchema],
) -> list[PendingServerAssetSchema]:
    assets: list[PendingServerAssetSchema] = []

    for server in servers:
        icon = server.server_snapshot.icon

        if icon is not None:
            assets.append(
                PendingServerAssetSchema(
                    owner=server.server_snapshot,
                    field=AssetField.ICON,
                    prefix=S3_ICON_PREFIX,
                    content_type="image/png",
                    source=icon,
                    is_base64=True,
                )
            )

        assets.extend(collect_player_assets(server.players.values()))

    return assets


async def prepare_asset(asset: PendingServerAssetSchema) -> None:
    if asset.is_base64:
        asset.data = decode_base64(asset.source)
        return

    asset.data = await download_by_url(asset.source)


async def prepare_assets(assets: list[PendingServerAssetSchema]) -> None:
    await asyncio.gather(*(prepare_asset(asset) for asset in assets))


async def upload_asset(asset: PendingServerAssetSchema) -> None:
    if asset.data is None:
        logger.warning(f"Asset data ({asset.field}) is None")
        setattr(asset.owner, asset.field.value, None)
        return

    key = await s3.upload_bytes(
        data=asset.data,
        object_name=None,
        prefix=asset.prefix,
        content_type=asset.content_type,
        deduplicate=True,
    )

    setattr(asset.owner, asset.field.value, key)


async def upload_assets(assets: list[PendingServerAssetSchema]) -> None:
    await asyncio.gather(*(upload_asset(asset) for asset in assets))


async def upload_servers(
    servers: list[ServerCheckSchema],
) -> None:
    assets = collect_assets(servers)

    await prepare_assets(assets)
    await upload_assets(assets)


async def upload_players(player_snapshots: list[PlayerSnapshotSchema]) -> None:
    assets = collect_player_assets(player_snapshots)

    await prepare_assets(assets)
    await upload_assets(assets)
