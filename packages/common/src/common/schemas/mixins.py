from datetime import datetime

from pydantic import BaseModel, Field


class TimestampMixin(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)


class LastSeenMixin(BaseModel):
    last_seen_at: datetime = Field(default_factory=datetime.utcnow)
