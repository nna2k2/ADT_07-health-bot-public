from __future__ import annotations

from sqlalchemy import text

from app.db.models import Base
from app.db.session import engine


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    # Lightweight SQLite migration for older demo DBs.
    with engine.begin() as conn:
        try:
            cols = conn.execute(text("PRAGMA table_info(appointments)")).fetchall()
            names = {str(c[1]) for c in cols}
            if "patient_phone" not in names:
                conn.execute(text("ALTER TABLE appointments ADD COLUMN patient_phone VARCHAR(32) NOT NULL DEFAULT ''"))
        except Exception:
            # Ignore when table doesn't exist yet or DB backend differs.
            pass

        # Reminders: add one-shot + date support (for appointment reminders)
        try:
            cols = conn.execute(text("PRAGMA table_info(reminders)")).fetchall()
            names = {str(c[1]) for c in cols}
            if "date_str" not in names:
                conn.execute(text("ALTER TABLE reminders ADD COLUMN date_str VARCHAR(10) NOT NULL DEFAULT ''"))
            if "one_shot" not in names:
                conn.execute(text("ALTER TABLE reminders ADD COLUMN one_shot BOOLEAN NOT NULL DEFAULT 0"))
        except Exception:
            pass
        try:
            # Ensure family_members exists in older DBs (create_all may not run if DB file already has tables).
            conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS family_members ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "owner_user_id VARCHAR(64) NOT NULL, "
                    "member_user_id VARCHAR(64) NOT NULL DEFAULT '', "
                    "name VARCHAR(64) NOT NULL, "
                    "relation VARCHAR(32) NOT NULL DEFAULT 'family', "
                    "age INTEGER NOT NULL DEFAULT 0, "
                    "gender VARCHAR(24) NOT NULL DEFAULT '', "
                    "height_cm FLOAT NOT NULL DEFAULT 0, "
                    "weight_kg FLOAT NOT NULL DEFAULT 0, "
                    "goal VARCHAR(255) NOT NULL DEFAULT '', "
                    "medical_notes TEXT NOT NULL DEFAULT '', "
                    "tracking_note VARCHAR(255) NOT NULL DEFAULT '', "
                    "avatar_bg VARCHAR(24) NOT NULL DEFAULT '#dcfce7', "
                    "facts_text TEXT NOT NULL DEFAULT '', "
                    "created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL"
                    ")"
                )
            )
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_family_members_owner_user_id ON family_members(owner_user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_family_members_member_user_id ON family_members(member_user_id)"))
        except Exception:
            pass

        # Add missing columns when table existed before.
        try:
            cols = conn.execute(text("PRAGMA table_info(family_members)")).fetchall()
            names = {str(c[1]) for c in cols}
            if "member_user_id" not in names:
                conn.execute(text("ALTER TABLE family_members ADD COLUMN member_user_id VARCHAR(64) NOT NULL DEFAULT ''"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_family_members_member_user_id ON family_members(member_user_id)"))
            if "gender" not in names:
                conn.execute(text("ALTER TABLE family_members ADD COLUMN gender VARCHAR(24) NOT NULL DEFAULT ''"))
            if "height_cm" not in names:
                conn.execute(text("ALTER TABLE family_members ADD COLUMN height_cm FLOAT NOT NULL DEFAULT 0"))
            if "weight_kg" not in names:
                conn.execute(text("ALTER TABLE family_members ADD COLUMN weight_kg FLOAT NOT NULL DEFAULT 0"))
            if "goal" not in names:
                conn.execute(text("ALTER TABLE family_members ADD COLUMN goal VARCHAR(255) NOT NULL DEFAULT ''"))
            if "medical_notes" not in names:
                conn.execute(text("ALTER TABLE family_members ADD COLUMN medical_notes TEXT NOT NULL DEFAULT ''"))
        except Exception:
            pass

