from common.models.server import ServerModel
from common.schemas.server import ServerCheckSchema
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession


async def get_next_server_group(db: AsyncSession) -> list[ServerModel]:
    subquery = (
        select(ServerModel.ip)
        .order_by(ServerModel.last_seen_at.asc())
        .limit(1)
        .scalar_subquery()
    )

    stmt = (
        update(ServerModel)
        .where(ServerModel.ip == subquery)
        .values(last_seen_at=func.now())
        .returning(ServerModel)
    )

    servers = (await db.execute(stmt)).scalars().all()

    return servers  # type: ignore


async def save_servers(
    db: AsyncSession,
    servers: list[tuple[ServerModel, ServerCheckSchema | None]],
    update_ip: bool,
    update_porter: bool,
) -> None:
    # TODO: overwrite last_porter and last_ip_chek datetimes
    for model, check in servers:  # noqa: B007
        if check is None:
            pass
            # TODO: end ServerSession
