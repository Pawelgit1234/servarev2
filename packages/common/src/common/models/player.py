from datetime import datetime
from typing import TYPE_CHECKING

from common.base import Base
from common.enums import PlayerType
from common.models.mixins import LastSeenMixin, TimestampMixin
from common.settings import USERNAME_MAX
from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from common.models.server import ServerModel


class PlayerModel(Base, TimestampMixin, LastSeenMixin):  # type: ignore
    __tablename__ = "players"
    __table_args__ = (
        Index("ix_players_player_type", "player_type"),
        Index("ix_players_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    player_type: Mapped[PlayerType] = mapped_column(
        Enum(PlayerType), nullable=False
    )
    uuid: Mapped[str] = mapped_column(
        nullable=False
    )  # not unique because of offline players

    snapshots: Mapped[list["PlayerSnapshotModel"]] = relationship(
        back_populates="player",
        cascade="all, delete-orphan",
    )
    sessions: Mapped[list["PlayerSessionModel"]] = relationship(
        back_populates="player",
        cascade="all, delete-orphan",
    )
    servers: Mapped[list["ServerPlayerAssociationModel"]] = relationship(
        back_populates="player",
        cascade="all, delete-orphan",
    )


class ServerPlayerAssociationModel(Base, TimestampMixin, LastSeenMixin):  # type: ignore
    __tablename__ = "server_player_associations"
    __table_args__ = (
        Index("ix_server_player_associations_player_id", "player_id"),
        Index("ix_server_player_associations_created_at", "created_at"),
    )

    server_id: Mapped[int] = mapped_column(
        ForeignKey("servers.id", ondelete="CASCADE"),
        primary_key=True,
    )
    server: Mapped["ServerModel"] = relationship(
        back_populates="players",
    )
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"),
        primary_key=True,
    )
    player: Mapped["PlayerModel"] = relationship(
        back_populates="servers",
    )


class PlayerSnapshotModel(Base, TimestampMixin):  # type: ignore
    __tablename__ = "player_snapshots"
    __table_args__ = (
        Index("ix_player_snapshots_name", "name"),
        Index("ix_player_snapshots_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"),
        index=True,
    )
    player: Mapped["PlayerModel"] = relationship(back_populates="snapshots")

    name: Mapped[str] = mapped_column(
        String(USERNAME_MAX), nullable=False
    )  # not unique because of offline players
    skin: Mapped[str | None] = mapped_column(String(32), nullable=True)  # hash
    cape: Mapped[str | None] = mapped_column(String(32), nullable=True)  # hash


class PlayerSessionModel(Base):  # type: ignore
    __tablename__ = "player_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)

    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"),
        index=True,
    )
    player: Mapped["PlayerModel"] = relationship(back_populates="sessions")

    from_: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    to: Mapped[datetime | None] = mapped_column(nullable=True)
