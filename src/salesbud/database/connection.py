"""
Database configuration and connection utilities
"""

import sqlite3
from contextlib import contextmanager
from typing import Generator, Optional

from salesbud.utils import logger
from salesbud.utils.paths import get_db_path

DB_PATH = get_db_path()
DB_PATH.parent.mkdir(exist_ok=True)

# Connection singleton for better performance and thread safety
_db_connection = None


@contextmanager
def get_db_cursor() -> Generator:
    """Context manager for database operations with automatic commit/rollback.

    Usage:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM leads")
            results = cursor.fetchall()
    """
    conn = get_db()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except sqlite3.Error:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()


@contextmanager
def db_transaction():
    """Context manager for database transactions with automatic commit/rollback.

    Usage:
        with db_transaction() as cursor:
            cursor.execute("INSERT INTO leads ...")
    """
    conn = get_db()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except sqlite3.Error:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()


def get_db():
    """Get database connection with row factory.

    Uses singleton pattern with WAL mode for better concurrency.
    """
    global _db_connection
    if _db_connection is None:
        _db_connection = sqlite3.connect(DB_PATH, check_same_thread=False)
        _db_connection.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrency
        _db_connection.execute("PRAGMA journal_mode=WAL")
        _db_connection.execute("PRAGMA synchronous=NORMAL")
    return _db_connection


def is_quiet_mode() -> bool:
    """Check if quiet mode is enabled (for JSON output)."""
    return logger.is_quiet()


def init_db():
    """Initialize database with schema."""
    conn = get_db()
    cursor = conn.cursor()

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
            pass

    for col, col_type, default in [
        ("company_url", "TEXT", None),
        ("company_description", "TEXT", None),
        ("company_size_est", "TEXT", None),
        ("buying_signals", "TEXT", None),
        ("enriched_at", "TEXT", None),
        ("email_source", "TEXT", None),
        ("email_verified", "INTEGER", "0"),
        ("company_research", "TEXT", None),
        ("personalization_angle", "TEXT", None),
    ]:
        try:
            if default is not None:
                cursor.execute(f"ALTER TABLE leads ADD COLUMN {col} {col_type} DEFAULT '{default}'")
            else:
                cursor.execute(f"ALTER TABLE leads ADD COLUMN {col} {col_type}")
        except sqlite3.OperationalError:
            pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER REFERENCES leads(id),
            activity_type TEXT NOT NULL,
            content TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('dry_run', '1')")
    cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('dms_per_hour', '8')")
    cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('dms_per_day', '50')")
    cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('delay_minutes', '5')")
    cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('delay_variance', '10')")
    cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('emails_per_hour', '10')")
    cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('emails_per_day', '50')")
    cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('email_delay_minutes', '2')")

    # Create indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at DESC)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email) WHERE email IS NOT NULL"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_leads_sequence ON leads(status, sequence_step, last_dm_sent_at)"
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_lead_id ON activities(lead_id)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_activities_created_at ON activities(created_at DESC)"
    )

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


# Override flag - set to True by CLI --dry-run to temporarily force dry_run behavior
_dry_run_override: bool = False


def is_dry_run() -> bool:
    """Check if running in dry-run mode."""
    if _dry_run_override:
        return True
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


def get_daily_count(action: str) -> int:
    """Return today's count for an action type ('connections', 'emails').
    Resets automatically when the stored date differs from today."""
    from datetime import date

    today = str(date.today())
    date_key = f"{action}_sent_date"
    count_key = f"{action}_sent_today"

    stored_date = get_config(date_key)
    if stored_date != today:
        # New day — reset
        set_config(date_key, today)
        set_config(count_key, "0")
        return 0

    val = get_config(count_key)
    return int(val) if val and val.isdigit() else 0


def increment_daily_count(action: str) -> int:
    """Increment today's count for an action and return the new value.

    Uses atomic UPSERT to prevent race conditions.
    """
    conn = get_db()
    cursor = conn.cursor()
    count_key = f"{action}_sent_today"

    # Atomic increment with UPSERT (SQLite 3.24.0+)
    cursor.execute(
        """
        INSERT INTO config (key, value) 
        VALUES (?, '1')
        ON CONFLICT(key) DO UPDATE 
        SET value = CAST(value AS INTEGER) + 1
        RETURNING value
    """,
        (count_key,),
    )

    result = cursor.fetchone()
    conn.commit()
    return int(result[0]) if result else 0


def cleanup_old_activities(days: int = 90):
    """Remove activities older than specified days to manage database size."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM activities WHERE created_at < datetime('now', '-{} days')".format(days)
    )
    deleted = cursor.rowcount
    conn.commit()
    return deleted
