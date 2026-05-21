from datetime import datetime

from common.enums import PlayerType
from common.schemas.mixins import LastSeenMixin, TimestampMixin
from pydantic import BaseModel, ConfigDict


class PlayerSchema(TimestampMixin, LastSeenMixin):  # type: ignore
    player_type: PlayerType
    uuid: str

    model_config = ConfigDict(frozen=True)


class PlayerSnapshotSchema(TimestampMixin):  # type: ignore
    name: str
    skin: str | None = None
    cape: str | None = None


class PlayerSessionSchema(BaseModel):  # type: ignore
    from_: datetime
    to: datetime | None = None
