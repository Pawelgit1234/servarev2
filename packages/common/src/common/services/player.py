from common.models.player import (
    PlayerModel,
    PlayerSessionModel,
    PlayerSnapshotModel,
)
from common.schemas.player import PlayerSchema
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, contains_eager


async def load_existing_players(
    db: AsyncSession, players: list[PlayerSchema]
) -> dict[PlayerSchema, PlayerModel]:
    uuids = {player.uuid for player in players}

    # loads also the last session und the last snapshot
    latest_snapshot = (
        select(PlayerSnapshotModel)
        .distinct(PlayerSnapshotModel.player_id)
        .order_by(
            PlayerSnapshotModel.player_id,
            PlayerSnapshotModel.created_at.desc(),
        )
        .subquery()
    )
    latest_snapshot_alias = aliased(
        PlayerSnapshotModel,
        latest_snapshot,
    )

    latest_session = (
        select(PlayerSessionModel)
        .distinct(PlayerSessionModel.player_id)
        .order_by(
            PlayerSessionModel.player_id,
            PlayerSessionModel.from_.desc(),
        )
        .subquery()
    )
    latest_session_alias = aliased(
        PlayerSessionModel,
        latest_session,
    )

    rows = (
        (
            await db.execute(
                select(PlayerModel)
                .where(PlayerModel.uuid.in_(uuids))
                .outerjoin(
                    latest_snapshot_alias,
                    latest_snapshot_alias.player_id == PlayerModel.id,
                )
                .outerjoin(
                    latest_session_alias,
                    latest_session_alias.player_id == PlayerModel.id,
                )
                .options(
                    contains_eager(
                        PlayerModel.snapshots,
                        alias=latest_snapshot_alias,
                    ),
                    contains_eager(
                        PlayerModel.sessions,
                        alias=latest_session_alias,
                    ),
                )
            )
        )
        .scalars()
        .unique()
        .all()
    )

    rows_map = {player.uuid: player for player in rows}

    return {
        player_schema: rows_map[player_schema.uuid]
        for player_schema in players
        if player_schema.uuid in rows_map
    }
