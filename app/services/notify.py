"""Lead notifications.

Every new lead is passed to each channel in CHANNELS. The log channel is
always active. The email channel activates automatically once SMTP_USER
and SMTP_PASSWORD are set in the environment — until then it's a silent
no-op, so nothing breaks if you haven't configured it (e.g. locally).
"""
import logging
import os
import smtplib
from email.message import EmailMessage

log = logging.getLogger("leads")


def _log_channel(lead_id, lead, detail_url=None):
    log.info("NEW LEAD #%s type=%s budget=%s timeline=%s contact=%s",
             lead_id, lead["project_type"], lead["budget"],
             lead["timeline"], lead["contact_method"])


def _email_channel(lead_id, lead, detail_url=None):
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    to_addr = os.environ.get("NOTIFY_EMAIL_TO", user)

    if not user or not password:
        return  # email not configured; silently skip

    msg = EmailMessage()
    msg["Subject"] = f"New project request #{lead_id}: {lead['project_type']}"
    msg["From"] = user
    msg["To"] = to_addr

    lines = [
        f"New project request received (#{lead_id}).",
        "",
        f"Name: {lead['name']}",
        f"Email: {lead['email']}",
        f"Phone: {lead.get('phone') or '-'}",
        f"Organization: {lead.get('organization') or '-'}",
        f"Project type: {lead['project_type']}",
        f"Budget: {lead['budget']}",
        f"Timeline: {lead['timeline']}",
        f"Preferred contact: {lead['contact_method']}",
        f"Came from: {lead.get('source_topic') or 'Direct'}",
        "",
        "Description:",
        lead["description"],
    ]
    if detail_url:
        lines += ["", f"View in admin: {detail_url}"]
    msg.set_content("\n".join(lines))

    with smtplib.SMTP(host, port, timeout=15) as server:
        server.starttls()
        server.login(user, password)
        server.send_message(msg)


CHANNELS = [_log_channel, _email_channel]


def notify_new_lead(lead_id, lead, detail_url=None):
    for channel in CHANNELS:
        try:
            channel(lead_id, lead, detail_url)
        except Exception:  # one broken channel must never lose the lead
            log.exception("Notification channel %s failed", channel.__name__)
