import sqlite3
import time

from flask import (Blueprint, abort, current_app, redirect, render_template,
                   request, session, url_for)

from ..forms.project_request import (BUDGETS, CONTACT_METHODS, PROJECT_TYPES,
                                     TIMELINES, clean, guess_project_type,
                                     validate)
from ..models.lead import create_lead
from ..services.notify import notify_new_lead
from ..utils.analytics import record
from ..utils.security import check_csrf, limiter

bp = Blueprint("contact", __name__)

MIN_FILL_SECONDS = 3  # a human needs longer than this to fill the form in


def _render(values, errors, status=200):
    return render_template("contact.html", values=values, errors=errors,
                           project_types=PROJECT_TYPES, budgets=BUDGETS,
                           timelines=TIMELINES, methods=CONTACT_METHODS), status


def _allow_submission():
    ip = request.remote_addr or "unknown"
    return (limiter.allow(f"lead-hour:{ip}", 5, 3600)
            and limiter.allow(f"lead-day:{ip}", 20, 86400))


@bp.route("/contact", methods=["GET", "POST"])
def form():
    if request.method == "GET":
        topic = clean(request.args.get("topic", ""))[:100]
        session["form_ts"] = int(time.time())
        values = {"source_topic": topic}
        guess = guess_project_type(topic)
        if guess:
            values["project_type"] = guess
        return _render(values, {})

    if not _allow_submission():
        abort(429)
    check_csrf()

    # Honeypot: real visitors never see or fill this field. Bots get a fake success.
    if request.form.get("website", "").strip():
        return redirect(url_for("contact.thanks"))

    values, errors = validate(request.form)

    started = session.get("form_ts")
    if not isinstance(started, int) or time.time() - started < MIN_FILL_SECONDS:
        errors["_form"] = "Please review your details and press send again."

    if errors:
        return _render(values, errors, 400)

    try:
        lead_id = create_lead(values)
    except sqlite3.Error:
        current_app.logger.exception("Could not save lead")
        return _render(values, {"_form": "Sorry, your request could not be saved. "
                                "Please email me directly instead."}, 500)

    notify_new_lead(lead_id, values)
    record("project_form_submitted", values["project_type"])
    session.pop("form_ts", None)
    return redirect(url_for("contact.thanks"))


@bp.route("/contact/thanks")
def thanks():
    return render_template("thanks.html")
