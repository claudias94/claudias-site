import math

from .db import get_db

STATUSES = ["NEW", "CONTACTED", "DISCUSSION", "PROPOSAL SENT",
            "NEGOTIATION", "WON", "LOST", "COMPLETED"]
PAGE_SIZE = 25


def create_lead(v):
    """Insert a validated lead using a parameterised query. Returns its id."""
    db = get_db()
    cur = db.execute(
        "INSERT INTO leads (name, email, phone, organization, project_type, "
        "budget, timeline, contact_method, description, source_topic) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (v["name"], v["email"], v["phone"], v["organization"], v["project_type"],
         v["budget"], v["timeline"], v["contact_method"], v["description"],
         v["source_topic"]),
    )
    db.commit()
    return cur.lastrowid


def _like(text):
    """Escape LIKE wildcards so a search for '%' matches only a literal '%'."""
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def status_counts():
    counts = {s: 0 for s in STATUSES}
    for row in get_db().execute("SELECT status, COUNT(*) AS n FROM leads GROUP BY status"):
        counts[row["status"]] = row["n"]
    return counts


def list_leads(status="", q="", page=1):
    """Return (rows, total, page, pages). All user input goes in as parameters."""
    where, params = [], []
    if status in STATUSES:
        where.append("status = ?")
        params.append(status)
    if q:
        like = _like(q)
        where.append("(name LIKE ? ESCAPE '\\' OR email LIKE ? ESCAPE '\\' "
                     "OR organization LIKE ? ESCAPE '\\')")
        params += [like, like, like]
    clause = ("WHERE " + " AND ".join(where)) if where else ""  # fixed text only

    db = get_db()
    total = db.execute(f"SELECT COUNT(*) FROM leads {clause}", params).fetchone()[0]
    pages = max(1, math.ceil(total / PAGE_SIZE))
    page = min(max(1, page), pages)
    rows = db.execute(
        f"SELECT * FROM leads {clause} ORDER BY id DESC LIMIT ? OFFSET ?",
        params + [PAGE_SIZE, (page - 1) * PAGE_SIZE]).fetchall()
    return [dict(r) for r in rows], total, page, pages


def get_lead(lead_id):
    row = get_db().execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    return dict(row) if row else None


def update_lead(lead_id, status, notes, follow_up_on):
    db = get_db()
    cur = db.execute(
        "UPDATE leads SET status = ?, notes = ?, follow_up_on = ?, "
        "updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now') WHERE id = ?",
        (status, notes, follow_up_on, lead_id))
    db.commit()
    return cur.rowcount == 1


def delete_lead(lead_id):
    db = get_db()
    cur = db.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
    db.commit()
    return cur.rowcount == 1
