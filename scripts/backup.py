#!/usr/bin/env python3
"""Back up the leads database and log files.

Usage:
    python3 scripts/backup.py [--keep N]

Copies instance/leads.db (using SQLite's own safe backup API, so it is
correct even while the app is running and writing to it), plus the audit
and notification logs, into backups/<timestamp>/. Keeps the most recent N
backups (default 14) and deletes older ones.

Run this by hand, or on a schedule with cron, e.g. nightly at 2am:
    0 2 * * * cd /path/to/claudias-site && venv/bin/python3 scripts/backup.py
"""
import argparse
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INSTANCE = ROOT / "instance"
BACKUPS = ROOT / "backups"


def backup_sqlite(src, dest):
    """Safe copy of a live SQLite database using the backup API."""
    src_conn = sqlite3.connect(str(src))
    dest_conn = sqlite3.connect(str(dest))
    with dest_conn:
        src_conn.backup(dest_conn)
    src_conn.close()
    dest_conn.close()


def run(keep):
    db = INSTANCE / "leads.db"
    if not db.exists():
        print(f"No database found at {db}. Nothing to back up.", file=sys.stderr)
        return 1

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = BACKUPS / stamp
    target.mkdir(parents=True, exist_ok=True)

    backup_sqlite(db, target / "leads.db")
    for name in ("audit.log", "notifications.log"):
        src = INSTANCE / name
        if src.exists():
            shutil.copy2(src, target / name)

    print(f"Backup written to {target}")

    existing = sorted((p for p in BACKUPS.iterdir() if p.is_dir()), reverse=True)
    for old in existing[keep:]:
        shutil.rmtree(old)
        print(f"Removed old backup {old}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keep", type=int, default=14,
                        help="Number of recent backups to keep (default 14).")
    args = parser.parse_args()
    sys.exit(run(args.keep))
