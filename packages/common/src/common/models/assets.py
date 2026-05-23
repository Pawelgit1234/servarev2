from typing import TYPE_CHECKING

from common.base import Base
from common.enums import ServerSoftwareType
from common.models.mixins import TimestampMixin
from common.settings import (
    MOD_NAME_MAX,
    MOD_VERSION_MAX,
    PLUGIN_NAME_MAX,
    RESOURCE_PACK_URL_MAX,
    SOFTWARE_VESION_MAX,
)
from sqlalchemy import Enum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from common.models.server import (
        ServerBotSnapshotModel,
        ServerSnapshotModel,
    )


class SoftwareModel(Base, TimestampMixin):  # type: ignore
    __tablename__ = "softwares"
    __table_args__ = (
        Index("ix_softwares_name", "name"),
        Index("ix_softwares_version", "version"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[ServerSoftwareType] = mapped_column(
        Enum(ServerSoftwareType), nullable=False
    )
    version: Mapped[str] = mapped_column(
        String(SOFTWARE_VESION_MAX), nullable=False
    )

    snapshots: Mapped[list["ServerSnapshotModel"]] = relationship(
        back_populates="software",
    )


class ResourcePackModel(Base, TimestampMixin):  # type: ignore
    __tablename__ = "resource_packs"

    id: Mapped[int] = mapped_column(primary_key=True)

    url: Mapped[str] = mapped_column(
        String(RESOURCE_PACK_URL_MAX), unique=True
    )
    hash: Mapped[str] = mapped_column(String(64))

    bot_snapshot_associations: Mapped[
        list["ServerBotSnapshotResourcePackAssociationModel"]
    ] = relationship(
        back_populates="resource_pack",
        cascade="all, delete-orphan",
    )


class ServerBotSnapshotResourcePackAssociationModel(Base, TimestampMixin):  # type: ignore
    __tablename__ = "server_bot_snapshot_resource_pack_associations"
    __table_args__ = (
        Index("ix_bot_rp_snapshot_id", "bot_snapshot_id"),
        Index("ix_bot_rp_pack_id", "resource_pack_id"),
    )

    bot_snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("server_bot_snapshots.id", ondelete="CASCADE"),
        primary_key=True,
    )
    bot_snapshot: Mapped["ServerBotSnapshotModel"] = relationship(
        back_populates="resource_pack_associations",
    )

    resource_pack_id: Mapped[int] = mapped_column(
        ForeignKey("resource_packs.id", ondelete="CASCADE"),
        primary_key=True,
    )
    resource_pack: Mapped["ResourcePackModel"] = relationship(
        back_populates="bot_snapshot_associations",
    )


class PluginModel(Base, TimestampMixin):  # type: ignore
    __tablename__ = "plugins"
    __table_args__ = (Index("ix_plugins_name", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(PLUGIN_NAME_MAX), nullable=False, unique=True
    )

    snapshot_associations: Mapped[
        list["ServerSnapshotPluginAssociationModel"]
    ] = relationship(
        back_populates="plugin",
        cascade="all, delete-orphan",
    )


class ServerSnapshotPluginAssociationModel(Base, TimestampMixin):  # type: ignore
    __tablename__ = "server_snapshot_plugin_associations"
    __table_args__ = (
        Index("ix_ss_plugin_snapshot_id", "snapshot_id"),
        Index("ix_ss_plugin_plugin_id", "plugin_id"),
    )

    snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("server_snapshots.id", ondelete="CASCADE"),
        primary_key=True,
    )
    snapshot: Mapped["ServerSnapshotModel"] = relationship(
        back_populates="plugin_associations",
    )

    plugin_id: Mapped[int] = mapped_column(
        ForeignKey("plugins.id", ondelete="CASCADE"),
        primary_key=True,
    )
    plugin: Mapped["PluginModel"] = relationship(
        back_populates="snapshot_associations",
    )


class ModModel(Base, TimestampMixin):  # type: ignore
    __tablename__ = "mods"
    __table_args__ = (
        Index("ix_mods_name", "name"),
        Index("ix_mods_name_version", "name", "version"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(MOD_NAME_MAX), nullable=False)
    version: Mapped[str] = mapped_column(
        String(MOD_VERSION_MAX), nullable=False
    )

    snapshot_associations: Mapped[
        list["ServerSnapshotModAssociationModel"]
    ] = relationship(
        back_populates="mod",
        cascade="all, delete-orphan",
    )

    bot_snapshot_associations: Mapped[
        list["ServerBotSnapshotModAssociationModel"]
    ] = relationship(
        back_populates="mod",
        cascade="all, delete-orphan",
    )


class ServerSnapshotModAssociationModel(Base, TimestampMixin):  # type: ignore
    __tablename__ = "server_snapshot_mod_associations"
    __table_args__ = (
        Index("ix_ss_mod_snapshot_id", "snapshot_id"),
        Index("ix_ss_mod_mod_id", "mod_id"),
    )

    snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("server_snapshots.id", ondelete="CASCADE"),
        primary_key=True,
    )
    snapshot: Mapped["ServerSnapshotModel"] = relationship(
        back_populates="mod_associations",
    )

    mod_id: Mapped[int] = mapped_column(
        ForeignKey("mods.id", ondelete="CASCADE"),
        primary_key=True,
    )
    mod: Mapped["ModModel"] = relationship(
        back_populates="snapshot_associations",
    )


class ServerBotSnapshotModAssociationModel(Base, TimestampMixin):  # type: ignore
    __tablename__ = "server_bot_snapshot_mod_associations"
    __table_args__ = (
        Index("ix_bot_mod_snapshot_id", "bot_snapshot_id"),
        Index("ix_bot_mod_mod_id", "mod_id"),
    )

    bot_snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("server_bot_snapshots.id", ondelete="CASCADE"),
        primary_key=True,
    )
    bot_snapshot: Mapped["ServerBotSnapshotModel"] = relationship(
        back_populates="mod_associations",
    )

    mod_id: Mapped[int] = mapped_column(
        ForeignKey("mods.id", ondelete="CASCADE"),
        primary_key=True,
    )
    mod: Mapped["ModModel"] = relationship(
        back_populates="bot_snapshot_associations",
    )
