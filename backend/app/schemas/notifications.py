from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationBase(BaseModel):
    kind: str = "reminder"
    title: str
    message: str = ""
    read: bool = False


class NotificationCreate(NotificationBase):
    pass


class NotificationOut(NotificationBase):
    id: int
    user_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

