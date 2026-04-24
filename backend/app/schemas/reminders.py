from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ReminderBase(BaseModel):
    title: str
    description: str | None = None
    # Optional for one-shot reminders (appointments). Format: YYYY-MM-DD
    date_str: str | None = None
    time_str: str  # HH:MM
    type: str = "habit" # 'medication' | 'habit' | 'appointment'
    is_active: bool = True
    one_shot: bool = False

class ReminderCreate(ReminderBase):
    pass

class ReminderUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    date_str: str | None = None
    time_str: str | None = None
    type: str | None = None
    is_active: bool | None = None
    one_shot: bool | None = None

class ReminderOut(ReminderBase):
    id: int
    user_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
