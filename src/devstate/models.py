from datetime import datetime, timezone
from enum import IntEnum
from pydantic import BaseModel, Field

def utc_now():
    return datetime.now(timezone.utc)

class Priority(IntEnum):
    P0 = 0
    P1 = 1
    P2 = 2
    P3 = 3
    P4 = 4

class EventIn(BaseModel):
    source: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=160)
    message: str = Field(default="", max_length=2000)
    priority: Priority = Priority.P2
    tags: list[str] = Field(default_factory=list)

class ProjectSnapshot(BaseModel):
    name: str
    path: str
    branch: str | None = None
    dirty_paths: list[str] = Field(default_factory=list)
    commit: str | None = None
    captured_at: datetime = Field(default_factory=utc_now)
