from common.base import Base
from common.models.mixins import TimestampMixin
from sqlalchemy.orm import Mapped, mapped_column


class SoftwareModel(Base, TimestampMixin):  # type: ignore
    __tablename__ = "softwares"

    id: Mapped[int] = mapped_column(primary_key=True)


class PluginModel(Base, TimestampMixin):  # type: ignore
    __tablename__ = "plugins"

    id: Mapped[int] = mapped_column(primary_key=True)


class ResourcePackModel(Base, TimestampMixin):  # type: ignore
    __tablename__ = "recourse_packs"

    id: Mapped[int] = mapped_column(primary_key=True)


class ModModel(Base, TimestampMixin):  # type: ignore
    __tablename__ = "mods"

    id: Mapped[int] = mapped_column(primary_key=True)
