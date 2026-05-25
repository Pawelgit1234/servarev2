from datetime import datetime
from typing import TYPE_CHECKING

from common.base import Base
from common.enums import DetectedServiceType, ProtocolType, ServerType
from common.models.mixins import LastSeenMixin, TimestampMixin
from common.settings import (
    ASN_MAX,
    CITY_MAX,
    COUNTRY_MAX,
    HOSTNAME_MAX,
    REGION_MAX,
    SERVER_GAMEMODE_MAX,
    SERVER_MAP_NAME_MAX,
    SERVER_MOTD_MAX,
    SERVER_VERSION_MAX,
)
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from common.models.assets import (
        ServerBotSnapshotModAssociationModel,
        ServerBotSnapshotResourcePackAssociationModel,
        ServerSnapshotModAssociationModel,
        ServerSnapshotPluginAssociationModel,
        SoftwareModel,
    )
    from common.models.player import ServerPlayerAssociationModel


class ServerModel(Base, TimestampMixin, LastSeenMixin):  # type: ignore
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
    is_lan: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_multiport: Mapped[bool] = mapped_column(Boolean, nullable=False)
    server_type: Mapped[ServerType] = mapped_column(
        Enum(ServerType), nullable=False
    )

    last_ip_check_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_porter_check_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Geo
    country: Mapped[str | None] = mapped_column(
        String(COUNTRY_MAX), nullable=True
    )
    region: Mapped[str | None] = mapped_column(
        String(REGION_MAX), nullable=True
    )
    city: Mapped[str | None] = mapped_column(String(CITY_MAX), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Other IP stuff
    hostname: Mapped[str | None] = mapped_column(
        String(HOSTNAME_MAX), nullable=True
    )
    asn: Mapped[str | None] = mapped_column(String(ASN_MAX), nullable=True)

    # relationships
    sessions: Mapped[list["ServerSessionModel"]] = relationship(
        back_populates="server",
        cascade="all, delete-orphan",
    )
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
    players: Mapped[list["ServerPlayerAssociationModel"]] = relationship(
        back_populates="server",
        cascade="all, delete-orphan",
    )
    ports: Mapped[list["ServerPortAssociationModel"]] = relationship(
        back_populates="server",
        cascade="all, delete-orphan",
    )


class ServerSessionModel(Base):  # type: ignore
    __tablename__ = "server_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)

    server_id: Mapped[int] = mapped_column(
        ForeignKey("servers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    server: Mapped["ServerModel"] = relationship(back_populates="sessions")

    from_: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    to: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )


class ServerPortModel(Base):  # type: ignore
    __tablename__ = "server_ports"
    __table_args__ = (
        Index(
            "ix_server_ports_protocol_type_port",
            "protocol_type",
            "port",
        ),
        Index(
            "ix_server_ports_detected_service_type",
            "detected_service_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    servers: Mapped[list["ServerPortAssociationModel"]] = relationship(
        back_populates="server_port",
        cascade="all, delete-orphan",
    )

    port: Mapped[int] = mapped_column(Integer, nullable=False)
    protocol_type: Mapped[ProtocolType] = mapped_column(
        Enum(ProtocolType), nullable=False
    )
    detected_service_type: Mapped[DetectedServiceType] = mapped_column(
        Enum(DetectedServiceType), nullable=False
    )


class ServerPortAssociationModel(Base, TimestampMixin):  # type: ignore
    __tablename__ = "server_port_associations"

    server_id: Mapped[int] = mapped_column(
        ForeignKey("servers.id", ondelete="CASCADE"),
        primary_key=True,
    )
    server: Mapped["ServerModel"] = relationship(
        back_populates="ports",
    )

    server_port_id: Mapped[int] = mapped_column(
        ForeignKey("server_ports.id", ondelete="CASCADE"),
        primary_key=True,
    )
    server_port: Mapped["ServerPortModel"] = relationship(
        back_populates="servers",
    )


class ServerSnapshotModel(Base, TimestampMixin):  # type: ignore
    __tablename__ = "server_snapshots"
    __table_args__ = (
        Index("ix_server_snapshots_version", "version"),
        Index("ix_server_snapshots_players_max", "players_max"),
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
    version: Mapped[str] = mapped_column(
        String(SERVER_VERSION_MAX), nullable=False
    )
    players_max: Mapped[int] = mapped_column(Integer, nullable=False)
    motd: Mapped[str] = mapped_column(String(SERVER_MOTD_MAX), nullable=False)
    latency: Mapped[float] = mapped_column(Float, nullable=False)

    # Java
    protocol: Mapped[int | None] = mapped_column(Integer, nullable=True)
    icon: Mapped[str | None] = mapped_column(
        String(32), nullable=True, index=True
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
    map_name: Mapped[str | None] = mapped_column(
        String(SERVER_MAP_NAME_MAX), nullable=True
    )

    # Bedrock
    gamemode: Mapped[str | None] = mapped_column(
        String(SERVER_GAMEMODE_MAX), nullable=True
    )

    plugin_associations: Mapped[
        list["ServerSnapshotPluginAssociationModel"]
    ] = relationship(
        back_populates="snapshot",
        cascade="all, delete-orphan",
    )

    mod_associations: Mapped[list["ServerSnapshotModAssociationModel"]] = (
        relationship(
            back_populates="snapshot",
            cascade="all, delete-orphan",
        )
    )

    software_id: Mapped[int | None] = mapped_column(
        ForeignKey("softwares.id", ondelete="SET NULL"),
        index=True,
    )
    software: Mapped["SoftwareModel"] = relationship(
        back_populates="snapshots",
    )


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

    subchunks: Mapped[list["SubchunkModel"]] = relationship(
        back_populates="bot_snapshot",
        cascade="all, delete-orphan",
    )

    resource_pack_associations: Mapped[
        list["ServerBotSnapshotResourcePackAssociationModel"]
    ] = relationship(
        back_populates="bot_snapshot",
        cascade="all, delete-orphan",
    )
    mod_associations: Mapped[list["ServerBotSnapshotModAssociationModel"]] = (
        relationship(
            back_populates="bot_snapshot",
            cascade="all, delete-orphan",
        )
    )


class SubchunkModel(Base, TimestampMixin):  # type: ignore
    __tablename__ = "subchunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    bot_snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("server_bot_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    bot_snapshot: Mapped["ServerBotSnapshotModel"] = relationship(
        back_populates="subchunks"
    )

    hash: Mapped[str] = mapped_column(String(32), index=True)
