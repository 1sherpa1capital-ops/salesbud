"""
Lead model and CRUD operations
"""

import sqlite3
from typing import Any, Dict, List, Optional

from salesbud.database import get_db


def get_all_leads() -> List[Dict[str, Any]]:
    """Get all leads ordered by creation date."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_lead_by_id(lead_id: int) -> Optional[Dict[str, Any]]:
    """Get a single lead by ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_leads_by_status(status: str) -> List[Dict[str, Any]]:
    """Get leads filtered by status."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads WHERE status = ? ORDER BY created_at DESC", (status,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_lead(
    linkedin_url: str,
    name: Optional[str] = None,
    headline: Optional[str] = None,
    company: Optional[str] = None,
    location: Optional[str] = None,
) -> int:
    """Add a new lead. Returns lead ID."""
    conn = get_db()
    cursor = conn.cursor()
    lead_id: int = 0
    try:
        cursor.execute(
            "INSERT INTO leads (linkedin_url, name, headline, company, location) VALUES (?, ?, ?, ?, ?)",
            (linkedin_url, name, headline, company, location),
        )
        conn.commit()
        lead_id = cursor.lastrowid or 0
    except sqlite3.IntegrityError:
        # Lead already exists, get existing ID
        cursor.execute("SELECT id FROM leads WHERE linkedin_url = ?", (linkedin_url,))
        row = cursor.fetchone()
        lead_id = row["id"] if row else 0
    finally:
        conn.close()
    return lead_id  # type: ignore[return-value]


def update_lead_status(lead_id: int, status: str, sequence_step: Optional[int] = None):
    """Update lead status and optionally sequence step."""
    conn = get_db()
    cursor = conn.cursor()
    if sequence_step is not None:
        cursor.execute(
            "UPDATE leads SET status = ?, sequence_step = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, sequence_step, lead_id),
        )
    else:
        cursor.execute(
            "UPDATE leads SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, lead_id),
        )
    conn.commit()
    conn.close()


def update_lead_dm_sent(lead_id: int, sequence_step: int):
    """Update lead after sending a DM."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE leads SET sequence_step = ?, last_dm_sent_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (sequence_step, lead_id),
    )
    conn.commit()
    conn.close()


def get_lead_stats() -> Dict[str, int]:
    """Get statistics about leads."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM leads")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'new'")
    new_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'active'")
    active_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leads WHERE status IN ('completed', 'booked')")
    completed_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'connection_requested'")
    connection_requested = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'connected'")
    connected_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'connection_declined'")
    declined_count = cursor.fetchone()[0]

    # Email stats
    cursor.execute("SELECT COUNT(*) FROM leads WHERE email IS NOT NULL AND email != ''")
    has_email = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leads WHERE email_sequence_step > 0")
    email_active = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leads WHERE email_sequence_step >= 4")
    email_completed = cursor.fetchone()[0]

    conn.close()

    return {
        "total": total,
        "new": new_count,
        "active": active_count,
        "completed": completed_count,
        "connection_requested": connection_requested,
        "connected": connected_count,
        "declined": declined_count,
        "has_email": has_email,
        "email_active": email_active,
        "email_completed": email_completed,
    }


def update_lead_email(lead_id: int, email: str):
    """Set or update the email address for a lead."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE leads SET email = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (email, lead_id)
    )
    conn.commit()
    conn.close()


def update_lead_email_sent(lead_id: int, email_step: int):
    """Update lead after sending a cold email."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE leads SET email_sequence_step = ?, last_email_sent_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (email_step, lead_id),
    )
    conn.commit()
    conn.close()


def update_lead_company_url(lead_id: int, company_url: str):
    """Set or update the company URL for a lead (used for enrichment)."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE leads SET company_url = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (company_url, lead_id),
    )
    conn.commit()
    conn.close()


def update_lead_research(lead_id: int, research_data: str):
    """Set or update the agent-browser research dump for a lead."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE leads SET company_research = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (research_data, lead_id),
    )
    conn.commit()
    conn.close()


def update_lead_personalization(lead_id: int, personalization: str):
    """Set or update the personalized icebreaker for a lead."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE leads SET personalization_angle = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (personalization, lead_id),
    )
    conn.commit()
    conn.close()
