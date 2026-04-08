from datetime import datetime

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column

from common.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Server(Base, TimestampMixin):  # type: ignore
    __tablename__ = "servers"

    id: Mapped[int] = mapped_column(primary_key=True)

    ip: Mapped[str] = mapped_column(INET, nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)


class ServerMotd(Base, TimestampMixin):  # type: ignore
    __tablename__ = "server_motds"

    id: Mapped[int] = mapped_column(primary_key=True)


class Player(Base, TimestampMixin):  # type: ignore
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True)


class PlayerSession(Base):  # type: ignore
    __tablename__ = "player_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)

    from_: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    to: Mapped[datetime] = mapped_column(nullable=True)
