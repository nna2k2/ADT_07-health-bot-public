from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.core.config import settings


def send_email(*, to_email: str, subject: str, body_text: str, body_html: str | None = None) -> None:
    host = (settings.smtp_host or "").strip()
    from_email = (settings.smtp_from or settings.smtp_user or "").strip()
    if not host or not from_email:
        # Demo mode: skip sending if SMTP not configured.
        return

    msg = EmailMessage()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body_text)
    if body_html:
        msg.add_alternative(body_html, subtype="html")

    with smtplib.SMTP(host, settings.smtp_port, timeout=15) as s:
        s.ehlo()
        try:
            s.starttls()
            s.ehlo()
        except Exception:
            # If server doesn't support STARTTLS, continue.
            pass
        user = (settings.smtp_user or "").strip()
        pwd = (settings.smtp_pass or "").strip()
        if user and pwd:
            s.login(user, pwd)
        s.send_message(msg)

