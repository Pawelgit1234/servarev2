from datetime import UTC, datetime

from pydantic import BaseModel, Field


class TimestampMixin(BaseModel):
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class LastSeenMixin(BaseModel):
    last_seen_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
