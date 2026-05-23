from common.enums import ServerSoftwareType
from common.schemas.mixins import TimestampMixin


class SoftwareSchema(TimestampMixin):  # type: ignore
    name: ServerSoftwareType
    version: str


class ResourcePackSchema(TimestampMixin):  # type: ignore
    url: str
    hash: str


class PluginSchema(TimestampMixin):  # type: ignore
    name: str


class ModSchema(TimestampMixin):  # type: ignore
    name: str
    version: str
