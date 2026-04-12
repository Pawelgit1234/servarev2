from datetime import datetime

from common.base import Base
from common.models.mixins import TimestampMixin
from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class PlayerModel(Base, TimestampMixin):  # type: ignore
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True)

    uuid: Mapped[str] = mapped_column(unique=True)


class PlayerSnapshotModel(Base, TimestampMixin):  # type: ignore
    __tablename__ = "player_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str]  # not unique because of offline players
    skin: Mapped[str]  # hash


class PlayerSessionModel(Base):  # type: ignore
    __tablename__ = "player_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)

    from_: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    to: Mapped[datetime | None]
