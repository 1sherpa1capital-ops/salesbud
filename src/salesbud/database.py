"""
Database configuration and utilities
"""

import salesbud.utils.logger as logger
import os
import sqlite3
from pathlib import Path
from typing import Optional

# Database path - store in data/ directory
DB_PATH = Path(__file__).parent.parent.parent / "data" / "salesbud.db"
DB_PATH.parent.mkdir(exist_ok=True)


def get_db():
    """Get database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def is_quiet_mode() -> bool:
    """Check if quiet mode is enabled (for JSON output)."""
    return logger.is_quiet()


def init_db():
    """Initialize database with schema."""
    conn = get_db()
    cursor = conn.cursor()

    # Leads table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            linkedin_url TEXT UNIQUE NOT NULL,
            name TEXT,
            headline TEXT,
            company TEXT,
            location TEXT,
            email TEXT,
            status TEXT DEFAULT 'new',
            sequence_step INTEGER DEFAULT 0,
            email_sequence_step INTEGER DEFAULT 0,
            last_dm_sent_at TEXT,
            last_email_sent_at TEXT,
            last_reply_at TEXT,
            booking_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Add email columns if they don't exist (for existing databases)
    for col, col_type, default in [
        ("email", "TEXT", None),
        ("email_sequence_step", "INTEGER", "0"),
        ("last_email_sent_at", "TEXT", None),
    ]:
        try:
            if default is not None:
                cursor.execute(f"ALTER TABLE leads ADD COLUMN {col} {col_type} DEFAULT '{default}'")
            else:
                cursor.execute(f"ALTER TABLE leads ADD COLUMN {col} {col_type}")
        except sqlite3.OperationalError:
            pass  # Column already exists

    # Add enrichment columns if they don't exist (for existing databases)
    for col, col_type, default in [
        ("company_url", "TEXT", None),
        ("company_description", "TEXT", None),
        ("company_size_est", "TEXT", None),
        ("buying_signals", "TEXT", None),
        ("enriched_at", "TEXT", None),
        ("email_source", "TEXT", None),
        ("email_verified", "INTEGER", "0"),
    ]:
        try:
            if default is not None:
                cursor.execute(f"ALTER TABLE leads ADD COLUMN {col} {col_type} DEFAULT '{default}'")
            else:
                cursor.execute(f"ALTER TABLE leads ADD COLUMN {col} {col_type}")
        except sqlite3.OperationalError:
            pass  # Column already exists

    # Activity log
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER REFERENCES leads(id),
            activity_type TEXT NOT NULL,
            content TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Config
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # Default config
    cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('dry_run', '1')")
    cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('dms_per_hour', '8')")
    cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('dms_per_day', '50')")
    cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('delay_minutes', '5')")
    cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('delay_variance', '10')")
    cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('emails_per_hour', '10')")
    cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('emails_per_day', '50')")
    cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('email_delay_minutes', '2')")

    conn.commit()
    conn.close()
    if not is_quiet_mode():
        logger.print_text(f"✓ Database initialized at {DB_PATH}")


def get_config(key: str) -> Optional[str]:
    """Get config value by key."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else None


def set_config(key: str, value: str):
    """Set config value."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()


def is_dry_run() -> bool:
    """Check if running in dry-run mode."""
    return get_config("dry_run") == "1"


def log_activity(lead_id: int, activity_type: str, content: str):
    """Log an activity for a lead."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO activities (lead_id, activity_type, content) VALUES (?, ?, ?)",
        (lead_id, activity_type, content),
    )
    conn.commit()
    conn.close()
