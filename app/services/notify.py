"""Lead notifications.

Every new lead is passed to each channel in CHANNELS. Only the log channel is
active. Email, Telegram, WhatsApp Business, Google Sheets or a CRM can be added
later as extra functions in this list once you have credentials for them.
The log deliberately excludes names, emails and message text.
"""
import logging

log = logging.getLogger("leads")


def _log_channel(lead_id, lead):
    log.info("NEW LEAD #%s type=%s budget=%s timeline=%s contact=%s",
             lead_id, lead["project_type"], lead["budget"],
             lead["timeline"], lead["contact_method"])


CHANNELS = [_log_channel]


def notify_new_lead(lead_id, lead):
    for channel in CHANNELS:
        try:
            channel(lead_id, lead)
        except Exception:  # one broken channel must never lose the lead
            log.exception("Notification channel %s failed", channel.__name__)
