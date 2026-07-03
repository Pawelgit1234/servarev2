import asyncio

from common.checks.player import download_by_url
from common.enums import AssetField
from common.models.server import ServerPortModel
from common.s3client import s3
from common.schemas.server import (
    PendingServerAssetSchema,
    ServerCheckSchema,
    ServerPortSchema,
)
from common.services.common import ensure_entity
from common.settings import S3_CAPE_PREFIX, S3_ICON_PREFIX, S3_SKIN_PREFIX
from common.utils import decode_base64
from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession


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

        for snapshot in server.players.values():
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


async def prepare_asset(asset: PendingServerAssetSchema) -> None:
    if asset.is_base64:
        asset.data = decode_base64(asset.source)
        return

    asset.data = await download_by_url(asset.source)


async def prepare_assets(assets: list[PendingServerAssetSchema]) -> None:
    await asyncio.gather(*(prepare_asset(asset) for asset in assets))


async def upload_asset(asset: PendingServerAssetSchema) -> None:
    if asset.data is None:
        return

    key = await s3.upload_bytes(
        data=asset.data,
        object_name=None,
        prefix=asset.prefix,
        content_type=asset.content_type,
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


async def load_existing_ports(
    db: AsyncSession,
    ports: list[ServerPortSchema],
) -> dict[ServerPortSchema, ServerPortModel]:
    port_keys = {
        (p.port, p.protocol_type, p.detected_service_type) for p in ports
    }

    rows = (
        (
            await db.execute(
                select(ServerPortModel).where(
                    tuple_(
                        ServerPortModel.port,
                        ServerPortModel.protocol_type,
                        ServerPortModel.detected_service_type,
                    ).in_(port_keys)
                )
            )
        )
        .scalars()
        .all()
    )

    rows_map = {
        (p.port, p.protocol_type, p.detected_service_type): p for p in rows
    }

    return {
        port_schema: rows_map[
            (
                port_schema.port,
                port_schema.protocol_type,
                port_schema.detected_service_type,
            )
        ]
        for port_schema in ports
        if (
            port_schema.port,
            port_schema.protocol_type,
            port_schema.detected_service_type,
        )
        in rows_map
    }


def ensure_port(
    db: AsyncSession,
    port_map: dict[ServerPortSchema, ServerPortModel],
    port_schema: ServerPortSchema,
) -> ServerPortModel:
    return ensure_entity(
        db,
        port_map,
        port_schema,
        lambda p: ServerPortModel(
            port=p.port,
            protocol_type=p.protocol_type,
            detected_service_type=p.detected_service_type,
        ),
    )
