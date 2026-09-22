import logging
import time
from datetime import datetime

from flask import (Blueprint, abort, current_app, flash, g, redirect,
                   render_template, request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from ..forms.project_request import clean
from ..models import admin as admins
from ..models import lead as leads
from ..utils.security import check_csrf, limiter

bp = Blueprint("admin", __name__, url_prefix="/admin")
audit = logging.getLogger("audit")

# Verified against when a username does not exist, so response time
# does not reveal which usernames are real.
_DUMMY_HASH = generate_password_hash("not-a-real-password")


@bp.before_request
def load_admin():
    """Every admin page except the sign-in page requires a valid session."""
    g.admin = None
    admin_id = session.get("admin_id")
    if admin_id:
        age = time.time() - session.get("login_ts", 0)
        if age <= current_app.config["ADMIN_MAX_SESSION_SECONDS"]:
            g.admin = admins.get_by_id(admin_id)
        if g.admin is None:
            session.clear()
    if g.admin is None and request.endpoint != "admin.login":
        return redirect(url_for("admin.login"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if g.admin:
        return redirect(url_for("admin.dashboard"))
    if request.method == "GET":
        return render_template("admin/login.html", error=None)

    ip = request.remote_addr or "unknown"
    if not limiter.allow(f"admin-login:{ip}", 10, 900):
        abort(429)
    check_csrf()

    username = clean(request.form.get("username", ""))[:64]
    password = request.form.get("password", "")[:256]
    now = int(time.time())

    account = admins.get_by_username(username)
    locked = bool(account and account["locked_until"] > now)
    valid = check_password_hash(account["password_hash"] if account else _DUMMY_HASH,
                                password)

    if account and valid and not locked:
        admins.reset_failures(account["id"])
        session.clear()  # new session on login prevents session fixation
        session.permanent = True
        session["admin_id"] = account["id"]
        session["login_ts"] = now
        audit.info("admin login ok admin_id=%s ip=%s", account["id"], ip)
        return redirect(url_for("admin.dashboard"))

    if account and not locked:
        admins.record_failure(account["id"], now)
    audit.warning("admin login failed ip=%s locked=%s", ip, locked)
    return render_template(
        "admin/login.html",
        error="Invalid username or password, or the account is temporarily locked."), 401


@bp.route("/logout", methods=["POST"])
def logout():
    check_csrf()
    audit.info("admin logout admin_id=%s", g.admin["id"])
    session.clear()
    return redirect(url_for("admin.login"))


@bp.route("/")
def dashboard():
    status = request.args.get("status", "")
    if status not in leads.STATUSES:
        status = ""
    q = clean(request.args.get("q", ""))[:100]
    try:
        page = int(request.args.get("page", "1"))
    except ValueError:
        page = 1
    rows, total, page, pages = leads.list_leads(status, q, page)
    counts = leads.status_counts()
    return render_template("admin/dashboard.html", rows=rows, total=total,
                           page=page, pages=pages, counts=counts,
                           total_all=sum(counts.values()), statuses=leads.STATUSES,
                           current_status=status, q=q)


def _validate_update(form):
    status = form.get("status", "")
    notes = clean(form.get("notes", ""), multiline=True)
    follow_up = clean(form.get("follow_up_on", ""))
    errors = {}
    if status not in leads.STATUSES:
        errors["status"] = "Choose a valid status."
    if len(notes) > 2000:
        errors["notes"] = "Notes can be up to 2000 characters."
    if follow_up:
        try:
            follow_up = datetime.strptime(follow_up, "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            errors["follow_up_on"] = "Please use a valid date."
    return {"status": status, "notes": notes, "follow_up_on": follow_up}, errors


@bp.route("/leads/<int:lead_id>", methods=["GET", "POST"])
def lead_detail(lead_id):
    lead = leads.get_lead(lead_id)
    if lead is None:
        abort(404)
    form, errors = lead, {}

    if request.method == "POST":
        check_csrf()
        form, errors = _validate_update(request.form)
        if not errors:
            leads.update_lead(lead_id, form["status"], form["notes"], form["follow_up_on"])
            audit.info("lead #%s updated status=%s->%s by admin_id=%s",
                       lead_id, lead["status"], form["status"], g.admin["id"])
            flash("Saved.", "ok")
            return redirect(url_for("admin.lead_detail", lead_id=lead_id))

    return render_template("admin/lead.html", lead=lead, form=form, errors=errors,
                           statuses=leads.STATUSES), (400 if errors else 200)


@bp.route("/leads/<int:lead_id>/delete", methods=["POST"])
def lead_delete(lead_id):
    check_csrf()
    if request.form.get("confirm") != "yes":
        flash("Tick the confirmation box to delete a lead.", "error")
        return redirect(url_for("admin.lead_detail", lead_id=lead_id))
    if not leads.delete_lead(lead_id):
        abort(404)
    audit.info("lead #%s deleted by admin_id=%s", lead_id, g.admin["id"])
    flash(f"Lead #{lead_id} deleted.", "ok")
    return redirect(url_for("admin.dashboard"))
