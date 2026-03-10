"""
Minimalist CLI Dashboard for SalesBud
Clean, simple, and readable TUI using Rich.
"""

import salesbud.utils.logger as logger
from typing import Optional
from rich.table import Table
from rich.console import Console
from rich import box

from salesbud.models.lead import get_all_leads, get_leads_by_status, get_lead_stats
from salesbud.database import get_config, is_dry_run

# Simple color scheme
STATUS_COLORS = {
    "new": "blue",
    "connection_requested": "yellow",
    "connected": "green",
    "active": "cyan",
    "replied": "magenta",
    "paused": "dim",
    "booked": "green",
    "completed": "dim",
    "connection_declined": "red",
}

console = Console()


def show_dashboard(filter_status: Optional[str] = None):
    """Display a clean, minimal dashboard."""
    dry_run = is_dry_run()
    mode = "DRY RUN" if dry_run else "LIVE"
    mode_color = "yellow" if dry_run else "red"

    # Simple header
    console.print(f"\n[bold]SalesBud[/bold] — {mode}\n", style=mode_color)

    stats = get_lead_stats()
    leads = get_all_leads()

    # Count statuses
    connection_requested = sum(1 for l in leads if l["status"] == "connection_requested")
    connected = sum(1 for l in leads if l["status"] == "connected")
    declined = sum(1 for l in leads if l["status"] == "connection_declined")

    # Simple stats line
    console.print(
        f"Leads: [bold]{stats['total']}[/bold] total | "
        f"[blue]{stats['new']}[/blue] new | "
        f"[yellow]{connection_requested}[/yellow] pending | "
        f"[green]{connected}[/green] connected | "
        f"[cyan]{stats['active']}[/cyan] active\n"
    )

    # Show leads table
    leads = get_all_leads() if not filter_status else get_leads_by_status(filter_status)

    if not leads:
        console.print("[dim]No leads found. Run 'scrape' to add leads.[/dim]\n")
        return

    # Clean, simple table
    table = Table(
        box=box.SIMPLE, show_header=True, header_style="bold", padding=(0, 1), expand=True
    )
    table.add_column("ID", justify="right", style="dim", width=4)
    table.add_column("Name", style="white", min_width=15)
    table.add_column("Status", width=12)
    table.add_column("DM", justify="center", width=4)
    table.add_column("Email", justify="center", width=5)
    table.add_column("Company", style="dim", min_width=12)

    for lead in leads[:50]:  # Show max 50
        lead_id = str(lead["id"])
        name = (lead.get("name") or "Unknown")[:20]
        status = lead["status"] or "new"
        dm_step = str(lead.get("sequence_step") or 0)
        e_step = "✓" if lead.get("email") else "·"
        company = (lead.get("company") or "—")[:18]

        color = STATUS_COLORS.get(status, "white")
        status_display = status.replace("_", " ")

        table.add_row(
            lead_id, name, f"[{color}]{status_display}[/{color}]", dm_step, e_step, company
        )

    if not logger.is_quiet():
        console.print(table)

        if len(leads) > 50:
            console.print(f"\n[dim]... and {len(leads) - 50} more[/dim]")

        console.print(
            "\n[dim]Commands: lead <id> | add-email <id> <email> | sequence | email-sequence[/dim]\n"
        )


def show_lead_detail(lead_id: int):
    """Show clean, minimal lead details."""
    from salesbud.models.lead import get_lead_by_id
    from salesbud.database import get_db

    lead = get_lead_by_id(lead_id)
    if not lead:
        console.print(f"[red]Lead {lead_id} not found[/red]\n")
        return

    # Simple header
    console.print(f"\n[bold]{lead.get('name', 'Unknown')}[/bold] — Lead #{lead_id}\n")

    # Details in simple format
    status = lead.get("status", "new")
    color = STATUS_COLORS.get(status, "white")

    console.print(f"Status:    [{color}]{status}[/{color}]")
    console.print(f"Company:   {lead.get('company') or '—'}")
    console.print(f"Headline:  {lead.get('headline') or '—'}")
    console.print(f"Location:  {lead.get('location') or '—'}")
    console.print(f"LinkedIn:  {lead.get('linkedin_url') or '—'}")
    console.print(f"Email:     {lead.get('email') or '[dim]not set[/dim]'}")
    console.print(f"DM Step:   {lead.get('sequence_step', 0)}/5")
    console.print(f"Email:     {lead.get('email_sequence_step', 0)}/4")

    # Activity
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM activities WHERE lead_id = ? ORDER BY created_at DESC LIMIT 5", (lead_id,)
    )
    activities = cursor.fetchall()
    conn.close()

    if activities:
        console.print("\n[bold]Recent Activity:[/bold]")
        for a in activities:
            time = str(a["created_at"]).split(".")[0]  # Remove microseconds
            act_type = a["activity_type"]
            content = (a["content"] or "")[:50]
            console.print(f"  [dim]{time}[/dim] [{act_type}] {content}")

    console.print()


def show_help():
    """Show clean, simple help."""
    if logger.is_quiet():
        return

    console.print("\n[bold]SalesBud CLI[/bold] — LinkedIn + Cold Email Automation\n")

    commands = [
        ("init", "Initialize database"),
        ("scrape", "Scrape LinkedIn leads"),
        ("connect", "Send connection requests"),
        ("check-connections", "Check pending connections"),
        ("sequence", "Run DM sequence step"),
        ("email-sequence", "Run email sequence step"),
        ("find-email <id>", "Find email for lead"),
        ("add-email <id> <email>", "Add email to lead"),
        ("enrich <id>", "Enrich lead company data"),
        ("workflow", "Full pipeline workflow"),
        ("dashboard", "Show lead dashboard"),
        ("lead <id>", "Show lead details"),
        ("status", "System status"),
    ]

    for cmd, desc in commands:
        console.print(f"  [cyan]{cmd:<25}[/cyan] {desc}")

    console.print("\n[dim]Examples:[/dim]")
    console.print("  uv run python -m salesbud scrape --query 'CEO' --location 'Austin'")
    console.print("  uv run python -m salesbud connect --max 10")
    console.print("  uv run python -m salesbud sequence\n")
