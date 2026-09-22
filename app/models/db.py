import os
import sqlite3

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL DEFAULT '',
    organization TEXT NOT NULL DEFAULT '',
    project_type TEXT NOT NULL,
    budget TEXT NOT NULL,
    timeline TEXT NOT NULL,
    contact_method TEXT NOT NULL,
    description TEXT NOT NULL,
    source_topic TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'NEW',
    notes TEXT NOT NULL DEFAULT '',
    follow_up_on TEXT NOT NULL DEFAULT '',
    updated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_created ON leads(created_at);

CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until INTEGER NOT NULL DEFAULT 0
);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def _migrate(conn):
    """Bring a database created by an earlier milestone up to date."""
    cols = {row[1] for row in conn.execute("PRAGMA table_info(leads)")}
    if "follow_up_on" not in cols:
        conn.execute("ALTER TABLE leads ADD COLUMN follow_up_on TEXT NOT NULL DEFAULT ''")
        conn.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        conn = get_db()
        conn.executescript(SCHEMA)
        _migrate(conn)
        close_db()
    try:
        os.chmod(app.config["DATABASE"], 0o600)  # owner read/write only
    except OSError:
        pass
