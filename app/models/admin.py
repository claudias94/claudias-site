from werkzeug.security import generate_password_hash

from .db import get_db

MAX_FAILED_ATTEMPTS = 5
LOCK_SECONDS = 15 * 60


def _one(row):
    return dict(row) if row else None


def get_by_username(username):
    return _one(get_db().execute(
        "SELECT * FROM admins WHERE username = ?", (username,)).fetchone())


def get_by_id(admin_id):
    return _one(get_db().execute(
        "SELECT * FROM admins WHERE id = ?", (admin_id,)).fetchone())


def create_admin(username, password):
    db = get_db()
    db.execute("INSERT INTO admins (username, password_hash) VALUES (?, ?)",
               (username, generate_password_hash(password)))
    db.commit()


def set_password(username, password):
    db = get_db()
    cur = db.execute(
        "UPDATE admins SET password_hash = ?, failed_attempts = 0, locked_until = 0 "
        "WHERE username = ?", (generate_password_hash(password), username))
    db.commit()
    return cur.rowcount == 1


def record_failure(admin_id, now):
    """Count a failed sign-in; lock the account after too many in a row."""
    db = get_db()
    row = db.execute("SELECT failed_attempts FROM admins WHERE id = ?",
                     (admin_id,)).fetchone()
    if row is None:
        return
    attempts = row["failed_attempts"] + 1
    if attempts >= MAX_FAILED_ATTEMPTS:
        db.execute("UPDATE admins SET failed_attempts = 0, locked_until = ? WHERE id = ?",
                   (now + LOCK_SECONDS, admin_id))
    else:
        db.execute("UPDATE admins SET failed_attempts = ? WHERE id = ?",
                   (attempts, admin_id))
    db.commit()


def reset_failures(admin_id):
    db = get_db()
    db.execute("UPDATE admins SET failed_attempts = 0, locked_until = 0 WHERE id = ?",
               (admin_id,))
    db.commit()
