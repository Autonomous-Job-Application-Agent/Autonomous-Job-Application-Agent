"""
database.py — SQLite logging for job applications.

Usage:
    python database.py          # View all logged applications
"""

import re
import sqlite3
import datetime
import os

from config import DB_PATH, create_dirs


# ── Schema ─────────────────────────────────────────────────────────────────────

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS applications (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    date          TEXT,
    job_title     TEXT,
    company       TEXT,
    job_url       TEXT,
    match_score   TEXT,
    status        TEXT DEFAULT 'Applied',
    resume_path   TEXT,
    cover_letter  TEXT
)
"""


# ── Core Functions ─────────────────────────────────────────────────────────────

def _get_conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(CREATE_TABLE_SQL)
    conn.commit()
    return conn


def log_application(
    job_title: str,
    company: str,
    job_url: str,
    gap_analysis: str,
    resume_path: str,
    cover_letter: str,
    status: str = "Applied",
) -> int:
    """Insert a new application record and return the new row id."""
    score_match = re.search(r"(\d{1,3})\s*%", gap_analysis)
    match_score = score_match.group(1) + "%" if score_match else "N/A"

    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO applications
           (date, job_title, company, job_url, match_score, status, resume_path, cover_letter)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            str(datetime.date.today()),
            job_title,
            company,
            job_url,
            match_score,
            status,
            resume_path,
            cover_letter[:1000],
        ),
    )
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    print(f"✅ Application logged! (id={row_id}, match score={match_score})")
    return row_id


def get_all_applications() -> list[dict]:
    """Return all application records as a list of dicts."""
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM applications ORDER BY date DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_status(app_id: int, new_status: str):
    """Update the status of an application (e.g. 'Interview', 'Offer', 'Rejected')."""
    conn = _get_conn()
    conn.execute("UPDATE applications SET status=? WHERE id=?", (new_status, app_id))
    conn.commit()
    conn.close()
    print(f"✅ Application {app_id} status updated to '{new_status}'.")


# ── CLI Entry Point ────────────────────────────────────────────────────────────

def main():
    create_dirs()
    apps = get_all_applications()
    if not apps:
        print("No applications logged yet.")
        return

    print(f"\n{'ID':<4} {'Date':<12} {'Company':<20} {'Title':<30} {'Score':<8} {'Status'}")
    print("-" * 85)
    for a in apps:
        print(
            f"{a['id']:<4} {a['date']:<12} {a['company'][:18]:<20} "
            f"{a['job_title'][:28]:<30} {a['match_score']:<8} {a['status']}"
        )


if __name__ == "__main__":
    main()