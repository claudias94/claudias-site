from flask import Blueprint, jsonify, request

from ..forms.project_request import clean
from ..utils.analytics import record
from ..utils.security import check_csrf, limiter

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/event", methods=["POST"])
def event():
    ip = request.remote_addr or "unknown"
    if not limiter.allow(f"event:{ip}", 60, 60):
        return jsonify(ok=False), 429
    data = request.get_json(silent=True) or {}
    check_csrf(str(data.get("csrf_token", "")))
    name = clean(str(data.get("event", "")))[:60]
    label = clean(str(data.get("label", "")))[:60]
    ok = record(name, label)
    return jsonify(ok=ok), (200 if ok else 400)
