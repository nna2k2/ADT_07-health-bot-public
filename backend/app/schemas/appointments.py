from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DoctorOut(BaseModel):
    id: int
    name: str
    specialty: str
    email: str
    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AppointmentCreate(BaseModel):
    user_id: str
    doctor_id: int
    patient_name: str
    patient_email: str
    patient_phone: str
    note: str | None = None
    date_str: str  # YYYY-MM-DD
    time_str: str  # HH:MM


class AppointmentOut(BaseModel):
    id: int
    user_id: str
    doctor_id: int
    patient_name: str
    patient_email: str
    patient_phone: str
    note: str | None = None
    date_str: str
    time_str: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

