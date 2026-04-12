from common.base import Base
from common.enums import ServerType
from common.models.mixins import TimestampMixin
from sqlalchemy import Boolean, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship


class ServerModel(Base, TimestampMixin):  # type: ignore
    __tablename__ = "servers"
    __table_args__ = (
        Index("ix_servers_ip", "ip"),
        Index("ix_servers_port", "port"),
        Index("ix_servers_server_type", "server_type"),
        Index("ix_servers_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    ip: Mapped[str] = mapped_column(INET, nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    server_type: Mapped[ServerType] = mapped_column(
        Enum(ServerType), nullable=False
    )

    # relationships
    snapshots: Mapped[list["ServerSnapshotModel"]] = relationship(
        back_populates="server",
        cascade="all, delete-orphan",
    )
    dynamic_snapshots: Mapped[list["ServerDynamicSnapshotModel"]] = (
        relationship(
            back_populates="server",
            cascade="all, delete-orphan",
        )
    )
    bot_snapshots: Mapped[list["ServerBotSnapshotModel"]] = relationship(
        back_populates="server",
        cascade="all, delete-orphan",
    )


class ServerSnapshotModel(Base, TimestampMixin):  # type: ignore
    __tablename__ = "server_snapshots"
    __table_args__ = (
        Index("ix_server_snapshots_is_online", "is_online"),
        Index("ix_server_snapshots_version", "version"),
        Index("ix_server_snapshots_players_max", "players_max"),
        Index("ix_server_snapshots_motd", "motd"),
        Index(
            "ix_server_snapshots_server_id_created_at",
            "server_id",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    server_id: Mapped[int] = mapped_column(
        ForeignKey("servers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    server: Mapped["ServerModel"] = relationship(back_populates="snapshots")

    # Common
    is_online: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    players_max: Mapped[int] = mapped_column(Integer, nullable=False)
    motd: Mapped[str] = mapped_column(String(512), nullable=False)
    latency: Mapped[int] = mapped_column(Integer, nullable=False)
    raw: Mapped[dict] = mapped_column(JSONB, nullable=False)  # type: ignore

    # Java
    protocol: Mapped[int | None] = mapped_column(Integer, nullable=True)
    favicon: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )  # hash
    enforcesSecureChat: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True
    )

    # Forge
    fml_network_version: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    mods_truncated: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Query / Bedrock
    map_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    gamemode: Mapped[str | None] = mapped_column(String(32), nullable=True)


class ServerDynamicSnapshotModel(Base, TimestampMixin):  # type: ignore
    __tablename__ = "server_dynamic_snapshots"
    __table_args__ = (
        Index("ix_server_dynamic_snapshots_players_online", "players_online"),
        Index(
            "ix_server_dynamic_snapshots_server_id_created_at",
            "server_id",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    server_id: Mapped[int] = mapped_column(
        ForeignKey("servers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    server: Mapped["ServerModel"] = relationship(
        back_populates="dynamic_snapshots"
    )

    players_online: Mapped[int] = mapped_column(Integer, nullable=False)


class ServerBotSnapshotModel(Base, TimestampMixin):  # type: ignore
    __tablename__ = "server_bot_snapshots"
    __table_args__ = (
        Index(
            "ix_server_bot_snapshots_server_id_created_at",
            "server_id",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    server_id: Mapped[int] = mapped_column(
        ForeignKey("servers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    server: Mapped["ServerModel"] = relationship(
        back_populates="bot_snapshots"
    )

    chunk_sections: Mapped[list["ChunkSectionModel"]] = relationship(
        back_populates="bot_snapshot",
        cascade="all, delete-orphan",
    )


class ChunkSectionModel(Base, TimestampMixin):  # type: ignore
    __tablename__ = "chunk_sections"

    id: Mapped[int] = mapped_column(primary_key=True)
    bot_snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("server_bot_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    bot_snapshot: Mapped["ServerBotSnapshotModel"] = relationship(
        back_populates="chunk_sections"
    )

    hash: Mapped[str] = mapped_column(String(64), index=True)
