"""
CLI Dashboard for SalesBud
Shows leads, status, DM and email sequence progress using Rich TUI.
"""
import salesbud.utils.logger as logger
from typing import Optional
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from salesbud.models.lead import get_all_leads, get_leads_by_status, get_lead_stats
from salesbud.database import get_config, is_dry_run
from salesbud.services.scraper import get_scraper_status

STATUS_COLORS = {
    "new": "blue",
    "connection_requested": "magenta",
    "connected": "green",
    "active": "cyan",
    "replied": "yellow",
    "paused": "yellow",
    "booked": "green",
    "completed": "dim",
    "connection_declined": "red",
}

def show_dashboard(filter_status: Optional[str] = None):
    """Display the lead dashboard with Rich."""
    dry_run = is_dry_run()
    mode_text = "[bold yellow]DRY RUN[/bold yellow]" if dry_run else "[bold green]PRODUCTION[/bold green]"
    
    logger.console.print(Panel.fit(
        f"[bold white]SALESBUD[/bold white] — Autonomous Outbound Agent\nMode: {mode_text}",
        border_style="magenta",
        box=box.ROUNDED
    ))
    
    stats = get_lead_stats()
    leads = get_all_leads()
    
    connection_requested = sum(1 for l in leads if l["status"] == "connection_requested")
    connected = sum(1 for l in leads if l["status"] == "connected")
    connection_declined = sum(1 for l in leads if l["status"] == "connection_declined")
    
    delay_min = int(get_config('delay_minutes') or 5)
    delay_var = int(get_config('delay_variance') or 10)
    
    summary_table = Table(box=box.SIMPLE_HEAD, show_header=False, expand=True)
    summary_table.add_column("Category", style="cyan", no_wrap=True)
    summary_table.add_column("Details")
    
    summary_table.add_row(
        "📊 Pipeline", 
        f"Total: [bold]{stats['total']}[/bold] | New: {stats['new']} | Conn Req: {connection_requested} | Connected: {connected}\n"
        f"Active: {stats['active']} | Completed: {stats['completed']} | Declined: {connection_declined}"
    )
    summary_table.add_row(
        "📧 Email",
        f"With email: {stats.get('has_email', 0)} | Sequencing: {stats.get('email_active', 0)} | Completed: {stats.get('email_completed', 0)}"
    )
    summary_table.add_row(
        "⚙️  Config",
        f"LinkedIn: {get_config('dms_per_hour')} DMs/hr, {get_config('dms_per_day')} DMs/day, {delay_min}-{delay_min + delay_var}min delay\n"
        f"Email: {get_config('emails_per_hour') or 10}/hr, {get_config('emails_per_day') or 50}/day"
    )
    
    if not logger.is_quiet():
        logger.console.print(summary_table)
    
    leads = get_all_leads() if not filter_status else get_leads_by_status(filter_status)
    
    table = Table(title=f"📋 Leads ({len(leads)})", box=box.ROUNDED, expand=True)
    table.add_column("ID", justify="right", style="dim")
    table.add_column("Name", style="white", no_wrap=True)
    table.add_column("Status", justify="center")
    table.add_column("DM Step", justify="center")
    table.add_column("Email Step", justify="center")
    table.add_column("Company", style="dim")
    table.add_column("📧", justify="center")
    
    for lead in leads:
        lead_id = str(lead["id"])
        name = (lead.get("name") or "Unknown")[:18]
        status = lead["status"] or "new"
        dm_step = f"{lead.get('sequence_step') or 0}/5"
        e_step = f"{lead.get('email_sequence_step') or 0}/4"
        company = (lead.get("company") or "-")[:15]
        has_email = "✓" if lead.get("email") else "-"
        
        color = STATUS_COLORS.get(status, "white")
        status_text = f"[{color}]{status}[/{color}]"
        
        table.add_row(lead_id, name, status_text, dm_step, e_step, company, has_email)
    
    if not logger.is_quiet():
        logger.console.print(table)
        logger.console.print("[dim]Use: salesbud lead <id> for details | add-email <id> <email> to add emails[/dim]")


def show_lead_detail(lead_id: int):
    """Show detailed info for a specific lead."""
    from salesbud.models.lead import get_lead_by_id
    from salesbud.database import get_db
    
    lead = get_lead_by_id(lead_id)
    if not lead:
        logger.error(f"Lead {lead_id} not found.")
        return
    
    details = Table.grid(padding=1)
    details.add_column(style="cyan", justify="right")
    details.add_column(style="white")
    
    details.add_row("Name:", lead.get('name'))
    details.add_row("Company:", lead.get('company'))
    details.add_row("Headline:", str(lead.get('headline')))
    details.add_row("Location:", str(lead.get('location')))
    details.add_row("LinkedIn:", f"[link={lead.get('linkedin_url')}]{lead.get('linkedin_url')}[/link]")
    details.add_row("Email:", lead.get('email') or "[dim]not set — use add-email[/dim]")
    
    status = lead.get('status', 'new')
    color = STATUS_COLORS.get(status, "white")
    details.add_row("Status:", f"[{color}]{status}[/{color}]")
    details.add_row("DM Step:", f"{lead.get('sequence_step', 0)}/5")
    details.add_row("Email Step:", f"{lead.get('email_sequence_step', 0)}/4")
    
    details.add_row("Last DM:", str(lead.get('last_dm_sent_at') or 'Never'))
    details.add_row("Last Email:", str(lead.get('last_email_sent_at') or 'Never'))
    details.add_row("Last Reply:", str(lead.get('last_reply_at') or 'Never'))
    details.add_row("Created:", str(lead.get('created_at')))
    
    if not logger.is_quiet():
        logger.console.print(Panel(details, title=f"Lead #{lead_id}", border_style="cyan", box=box.ROUNDED))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM activities WHERE lead_id = ? ORDER BY created_at DESC LIMIT 10", (lead_id,))
    activities = cursor.fetchall()
    conn.close()
    
    if activities and not logger.is_quiet():
        act_table = Table(title="Recent Activity", box=box.SIMPLE, show_header=False)
        act_table.add_column("Time", style="dim")
        act_table.add_column("Type", style="magenta")
        act_table.add_column("Content")
        
        for a in activities:
            content = (a['content'] or '')[:60]
            act_table.add_row(str(a['created_at']), str(a['activity_type']), content)
            
        logger.console.print(act_table)


def show_help():
    """Show CLI help."""
    if logger.is_quiet():
        return
        
    logger.console.print(Panel.fit(
        "[bold white]SalesBud CLI[/bold white] — LinkedIn DMs + Cold Email Sequences",
        border_style="magenta",
        box=box.ROUNDED
    ))
    
    logger.print_text("""
[bold]Usage:[/bold]
  python -m salesbud init                    Initialize database
  python -m salesbud scrape                  Scrape leads from LinkedIn
  python -m salesbud connect                 Send connection requests
  python -m salesbud check-connections       Check pending connection status
  python -m salesbud sequence                Run next LinkedIn DM sequence step
  python -m salesbud email --to X -s X -b X  Send a single test email via Resend
  python -m salesbud email-sequence          Run next cold email sequence step
  python -m salesbud add-email <id> <email>  Add email address to a lead
  python -m salesbud workflow                Full workflow: scrape → connect → DM → email
  python -m salesbud dashboard               Show lead dashboard
  python -m salesbud lead <id>               Show lead details
  python -m salesbud reply <id>              Simulate a reply (dry run)
  python -m salesbud status                  Show system and agent mode status

[bold]Workflow:[/bold]
  1. Scrape leads:        python -m salesbud scrape --query "CEO" --location "Austin"
  2. Add emails:          python -m salesbud add-email 1 sarah@company.com
  3. Send connections:    python -m salesbud connect --max 10
  4. Check accepts:       python -m salesbud check-connections
  5. DM sequence:         python -m salesbud sequence
  6. Email sequence:      python -m salesbud email-sequence
  
  Or run full workflow:   python -m salesbud workflow --query "CEO"
""")
