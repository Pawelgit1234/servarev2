from common.enums import ServerSoftwareType
from common.schemas.mixins import TimestampMixin
from pydantic import ConfigDict


class SoftwareSchema(TimestampMixin):  # type: ignore
    model_config = ConfigDict(frozen=True)

    name: ServerSoftwareType
    version: str


class ResourcePackSchema(TimestampMixin):  # type: ignore
    model_config = ConfigDict(frozen=True)

    url: str
    hash: str


class PluginSchema(TimestampMixin):  # type: ignore
    model_config = ConfigDict(frozen=True)

    name: str


class ModSchema(TimestampMixin):  # type: ignore
    model_config = ConfigDict(frozen=True)

    name: str
    version: str
