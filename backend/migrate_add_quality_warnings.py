#!/usr/bin/env python3
"""Migration: add `quality_warnings` column to the jobs table.

Stores a JSON-encoded list of human-readable OMR quality signals surfaced to
the user (e.g. "No measures detected", Audiveris WARN/ERROR excerpts). Safe to
run more than once — the column is added only if missing.

Usage:
    python3 migrate_add_quality_warnings.py
"""

import os
import sqlite3
import sys


def run_migration() -> int:
    db_path = os.path.join(os.path.dirname(__file__), "storage", "scorescan.db")
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(jobs)")
        columns = {row[1] for row in cur.fetchall()}

        if "quality_warnings" in columns:
            print("Column `quality_warnings` already exists — nothing to do.")
            return 0

        print("Adding `quality_warnings` column to jobs table...")
        cur.execute("ALTER TABLE jobs ADD COLUMN quality_warnings TEXT")
        conn.commit()
        print("Done.")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(run_migration())
