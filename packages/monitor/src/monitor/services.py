from common.checks.ip import get_ip_info
from common.databases import ra
from common.models.assets import (
    ServerSnapshotModAssociationModel,
    ServerSnapshotPluginAssociationModel,
)
from common.models.player import (
    PlayerModel,
    PlayerSessionModel,
    PlayerSnapshotModel,
)
from common.models.server import (
    IpModel,
    ServerDynamicSnapshotModel,
    ServerModel,
    ServerSessionModel,
    ServerSnapshotModel,
)
from common.schemas.ip import IpInfoSchema
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

    latest_snapshot = (
        select(ServerSnapshotModel)
        .distinct(ServerSnapshotModel.server_id)
        .order_by(
            ServerSnapshotModel.server_id,
            ServerSnapshotModel.created_at.desc(),
        )
        .subquery()
    )
    latest_snapshot_alias = aliased(ServerSnapshotModel, latest_snapshot)

    latest_dynamic_snapshot = (
        select(ServerDynamicSnapshotModel)
        .distinct(ServerDynamicSnapshotModel.server_id)
        .order_by(
            ServerDynamicSnapshotModel.server_id,
            ServerDynamicSnapshotModel.created_at.desc(),
        )
        .subquery()
    )
    latest_dynamic_snapshot_alias = aliased(
        ServerDynamicSnapshotModel, latest_dynamic_snapshot
    )

    latest_session = (
        select(ServerSessionModel)
        .distinct(ServerSessionModel.server_id)
        .order_by(
            ServerSessionModel.server_id, ServerSessionModel.from_.desc()
        )
        .subquery()
    )
    latest_session_alias = aliased(ServerSessionModel, latest_session)

    latest_player_session = (
        select(PlayerSessionModel)
        .join(PlayerModel, PlayerModel.id == PlayerSessionModel.player_id)
        .distinct(PlayerModel.uuid)
        .order_by(PlayerModel.uuid, PlayerSessionModel.from_.desc())
        .subquery()
    )
    latest_player_session_alias = aliased(
        PlayerSessionModel, latest_player_session
    )

    player_alias = aliased(PlayerModel)

    latest_player_snapshot = (
        select(PlayerSnapshotModel)
        .distinct(PlayerSnapshotModel.player_id)
        .order_by(
            PlayerSnapshotModel.player_id,
            PlayerSnapshotModel.created_at.desc(),
        )
        .subquery()
    )
    latest_player_snapshot_alias = aliased(
        PlayerSnapshotModel, latest_player_snapshot
    )

    stmt = (
        select(IpModel)
        .where(IpModel.id.in_(select(updated_ip.c.id)))
        .outerjoin(IpModel.servers)
        .outerjoin(
            latest_snapshot_alias,
            latest_snapshot_alias.server_id == ServerModel.id,
        )
        .outerjoin(
            latest_dynamic_snapshot_alias,
            latest_dynamic_snapshot_alias.server_id == ServerModel.id,
        )
        .outerjoin(
            latest_session_alias,
            latest_session_alias.server_id == ServerModel.id,
        )
        .outerjoin(
            latest_player_session_alias,
            latest_player_session_alias.server_id == ServerModel.id,
        )
        .outerjoin(
            player_alias,
            player_alias.id == latest_player_session_alias.player_id,
        )
        .outerjoin(
            latest_player_snapshot_alias,
            latest_player_snapshot_alias.player_id == player_alias.id,
        )
        .options(
            contains_eager(IpModel.servers),
            contains_eager(
                IpModel.servers,
            )
            .contains_eager(
                ServerModel.snapshots,
                alias=latest_snapshot_alias,
            )
            .selectinload(
                ServerSnapshotModel.software,
            ),
            contains_eager(
                IpModel.servers,
            )
            .contains_eager(
                ServerModel.snapshots,
                alias=latest_snapshot_alias,
            )
            .selectinload(
                ServerSnapshotModel.plugin_associations,
            )
            .selectinload(
                ServerSnapshotPluginAssociationModel.plugin,
            ),
            contains_eager(
                IpModel.servers,
            )
            .contains_eager(
                ServerModel.snapshots,
                alias=latest_snapshot_alias,
            )
            .selectinload(
                ServerSnapshotModel.mod_associations,
            )
            .selectinload(
                ServerSnapshotModAssociationModel.mod,
            ),
            contains_eager(
                IpModel.servers,
            ).contains_eager(
                ServerModel.dynamic_snapshots,
                alias=latest_dynamic_snapshot_alias,
            ),
            contains_eager(
                IpModel.servers,
            ).contains_eager(
                ServerModel.sessions,
                alias=latest_session_alias,
            ),
            contains_eager(
                IpModel.servers,
            )
            .contains_eager(
                ServerModel.player_sessions,
                alias=latest_player_session_alias,
            )
            .contains_eager(
                PlayerSessionModel.player,
                alias=player_alias,
            )
            .contains_eager(
                PlayerModel.snapshots,
                alias=latest_player_snapshot_alias,
            ),
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
