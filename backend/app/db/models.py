from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str] = mapped_column(String(24), nullable=False)
    height_cm: Mapped[float] = mapped_column(Float, nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    goal: Mapped[str] = mapped_column(String(255), nullable=False)
    medical_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Checkin(Base):
    __tablename__ = "checkins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    sleep_hours: Mapped[float] = mapped_column(Float, nullable=False)
    water_liters: Mapped[float] = mapped_column(Float, nullable=False)
    steps: Mapped[int] = mapped_column(Integer, nullable=False)
    mood: Mapped[str] = mapped_column(String(64), nullable=False)
    symptoms: Mapped[str] = mapped_column(Text, nullable=False, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    # Optional date for one-shot reminders (appointments). Format: YYYY-MM-DD
    date_str: Mapped[str] = mapped_column(String(10), nullable=False, default="")
    time_str: Mapped[str] = mapped_column(String(5), nullable=False)  # HH:MM format
    type: Mapped[str] = mapped_column(String(50), nullable=False, default="habit")  # 'medication' or 'habit'
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    one_shot: Mapped[bool] = mapped_column(nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    kind: Mapped[str] = mapped_column(String(32), nullable=False, default="reminder")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    read: Mapped[bool] = mapped_column(nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    specialty: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    email: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    avatar_url: Mapped[str] = mapped_column(String(512), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    doctor_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)

    patient_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    patient_email: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    patient_phone: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    note: Mapped[str] = mapped_column(Text, nullable=True)

    date_str: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
    time_str: Mapped[str] = mapped_column(String(5), nullable=False)  # HH:MM
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")  # pending/confirmed/declined

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class FamilyMember(Base):
    __tablename__ = "family_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    # Synthetic user_id used by bot/checkin/summary when switching profile.
    member_user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False, default="")

    name: Mapped[str] = mapped_column(String(64), nullable=False)
    relation: Mapped[str] = mapped_column(String(32), nullable=False, default="family")
    age: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    gender: Mapped[str] = mapped_column(String(24), nullable=False, default="")
    height_cm: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    goal: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    medical_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tracking_note: Mapped[str] = mapped_column(String(255), nullable=False, default="")

    avatar_bg: Mapped[str] = mapped_column(String(24), nullable=False, default="#dcfce7")

    # Simple display facts for the detail screen (Figma): store as newline-separated text.
    facts_text: Mapped[str] = mapped_column(Text, nullable=False, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
