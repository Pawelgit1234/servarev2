from common.checks.ip import get_ip_info
from common.databases import ra
from common.enums import PlayerType
from common.models.player import PlayerModel, PlayerSnapshotModel
from common.models.server import IpModel
from common.schemas.ip import IpInfoSchema
from common.services.server import _build_ip_with_latest_relations_stmt
from common.settings import (
    IP_CHECK_INTERVAL_DAYS,
    PORTER_CHECK_INTERVAL_DAYS,
    REDIS_PORTER_QUEUE,
)
from common.utils import has_expired
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, contains_eager


async def get_next_ip(
    db: AsyncSession,
) -> IpModel | None:
    locked_ip_subquery = (
        select(IpModel.id)
        .order_by(IpModel.last_seen_at.asc())
        .limit(1)
        .with_for_update(skip_locked=True)
        .scalar_subquery()
    )

    updated_ip = (
        update(IpModel)
        .where(IpModel.id == locked_ip_subquery)
        .values(last_seen_at=func.now())
        .returning(IpModel.id)
        .cte("updated_ip")
    )

    stmt = _build_ip_with_latest_relations_stmt(
        IpModel.id.in_(select(updated_ip.c.id))
    )

    return (await db.execute(stmt)).scalars().unique().one_or_none()


async def get_next_premium_player(db: AsyncSession) -> PlayerModel | None:
    locked_player_subquery = (
        select(PlayerModel.id)
        .where(PlayerModel.player_type == PlayerType.PREMIUM)
        .order_by(PlayerModel.last_seen_at.asc())
        .limit(1)
        .with_for_update(skip_locked=True)
        .scalar_subquery()
    )

    updated_player = (
        update(PlayerModel)
        .where(PlayerModel.id == locked_player_subquery)
        .values(last_seen_at=func.now())
        .returning(PlayerModel.id)
        .cte("updated_player")
    )

    latest_snapshot = (
        select(PlayerSnapshotModel)
        .distinct(PlayerSnapshotModel.player_id)
        .order_by(
            PlayerSnapshotModel.player_id,
            PlayerSnapshotModel.created_at.desc(),
        )
        .subquery()
    )
    latest_snapshot_alias = aliased(PlayerSnapshotModel, latest_snapshot)

    stmt = (
        select(PlayerModel)
        .where(PlayerModel.id.in_(select(updated_player.c.id)))
        .outerjoin(
            latest_snapshot_alias,
            latest_snapshot_alias.player_id == PlayerModel.id,
        )
        .options(
            contains_eager(PlayerModel.snapshots, alias=latest_snapshot_alias),
        )
    )

    return (await db.execute(stmt)).scalars().unique().one_or_none()


async def prepare_ip_data(ip: IpModel) -> tuple[IpInfoSchema | None, bool]:
    ip_info = None
    update_porter = False

    if has_expired(
        ip.last_ip_check_at,
        IP_CHECK_INTERVAL_DAYS,  # type: ignore
    ):
        ip_info = await get_ip_info(ip.ip)

    if (
        has_expired(
            ip.last_porter_check_at,
            PORTER_CHECK_INTERVAL_DAYS,  # type: ignore
        )
        and not ip.is_multiport
    ):
        await ra.rpush(REDIS_PORTER_QUEUE, ip.ip)  # type: ignore
        update_porter = True

    return ip_info, update_porter
