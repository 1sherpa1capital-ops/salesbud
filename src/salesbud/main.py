#!/usr/bin/env python3
"""
SalesBud CLI - Main Entry Point
LinkedIn DM Sequencer + Cold Email via Resend
"""

import salesbud.utils.logger as logger
import sys
import json
import argparse
from typing import Optional

from salesbud.database import init_db, get_config, set_config, is_dry_run
from salesbud.services.scraper import scrape_leads
from salesbud.services.sequence import (
    run_sequence_step,
    start_sequence_for_lead,
    simulate_reply,
    get_leads_due_for_step,
)
from salesbud.services.connector import run_connection_campaign, check_pending_connections
from salesbud.services.emailer import (
    send_email,
    run_email_sequence_step,
    start_email_sequence_for_lead,
    get_leads_due_for_email,
    get_leads_ready_for_email_start,
)
from salesbud.cli.dashboard import show_dashboard, show_lead_detail, show_help


EXIT_CODE_SUCCESS = 0
EXIT_CODE_ERROR = 1
EXIT_CODE_RATE_LIMITED = 2
EXIT_CODE_NOTHING_TO_PROCESS = 3

# Global flag to suppress prints when JSON output is requested


def set_quiet_mode(quiet: bool):
    """Enable/disable quiet mode to suppress print statements."""
    from salesbud.utils import logger

    logger.set_quiet_mode(quiet)


def print_json(success: bool, count: int, data: list, errors: Optional[list] = None):
    """Print JSON output for machine-readable response."""
    if errors is None:
        errors = []
    import sys

    sys.stdout.write(
        json.dumps({"success": success, "count": count, "data": data, "errors": errors}) + "\n"
    )


def main():
    parser = argparse.ArgumentParser(description="SalesBud - LinkedIn DM Sequencer + Cold Email")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # init
    init_parser = subparsers.add_parser("init", help="Initialize database")
    init_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # scrape
    scrape_parser = subparsers.add_parser("scrape", help="Scrape leads from LinkedIn")
    scrape_parser.add_argument("--json", action="store_true", help="Output as JSON")
    scrape_parser.add_argument("--query", "-q", default="CEO", help="Job title search")
    scrape_parser.add_argument("--location", "-l", default="Austin, TX", help="Location")
    scrape_parser.add_argument("--max", "-m", type=int, default=50, help="Max leads")

    # connect
    connect_parser = subparsers.add_parser("connect", help="Send connection requests")
    connect_parser.add_argument("--json", action="store_true", help="Output as JSON")
    connect_parser.add_argument("--max", "-m", type=int, default=10, help="Max connections")
    connect_parser.add_argument(
        "--delay", "-d", type=int, default=60, help="Delay between requests (seconds)"
    )

    # check-connections
    check_conn_parser = subparsers.add_parser(
        "check-connections", help="Check status of pending connections"
    )
    check_conn_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # sequence
    seq_parser = subparsers.add_parser("sequence", help="Run next DM sequence step")
    seq_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # email (send single email)
    email_parser = subparsers.add_parser("email", help="Send a single email via Resend")
    email_parser.add_argument("--json", action="store_true", help="Output as JSON")
    email_parser.add_argument("--to", required=True, help="Recipient email address")
    email_parser.add_argument("--subject", "-s", required=True, help="Email subject")
    email_parser.add_argument("--body", "-b", required=True, help="Email body text")

    # email-sequence
    email_seq_parser = subparsers.add_parser(
        "email-sequence", help="Run next cold email sequence step"
    )
    email_seq_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # add-email
    add_email_parser = subparsers.add_parser("add-email", help="Add email address to a lead")
    add_email_parser.add_argument("--json", action="store_true", help="Output as JSON")
    add_email_parser.add_argument("lead_id", type=int, help="Lead ID")
    add_email_parser.add_argument("email_address", help="Email address")

    # find-email
    find_email_parser = subparsers.add_parser("find-email", help="Find email for a specific lead")
    find_email_parser.add_argument("--json", action="store_true", help="Output as JSON")
    find_email_parser.add_argument("--quick", "-q", action="store_true", help="Quick mode (<10s)")
    find_email_parser.add_argument("lead_id", type=int, help="Lead ID")

    # find-emails
    find_emails_parser = subparsers.add_parser(
        "find-emails", help="Find emails for leads without emails"
    )
    find_emails_parser.add_argument("--json", action="store_true", help="Output as JSON")
    find_emails_parser.add_argument(
        "--quick", "-q", action="store_true", help="Quick mode with parallel processing"
    )
    find_emails_parser.add_argument("--max", "-m", type=int, default=10, help="Max leads")

    # workflow
    workflow_parser = subparsers.add_parser(
        "workflow", help="Full workflow: scrape → connect → check → sequence → email"
    )
    workflow_parser.add_argument("--json", action="store_true", help="Output as JSON")
    workflow_parser.add_argument("--query", "-q", default="CEO", help="Search query")
    workflow_parser.add_argument("--location", "-l", default="Austin, TX", help="Location")
    workflow_parser.add_argument("--max-leads", type=int, default=10, help="Max leads to scrape")
    workflow_parser.add_argument(
        "--max-connections", type=int, default=5, help="Max connection requests"
    )

    # dashboard
    dashboard_parser = subparsers.add_parser("dashboard", help="Show dashboard")
    dashboard_parser.add_argument("--json", action="store_true", help="Output as JSON")
    dashboard_parser.add_argument("--status", "-s", help="Filter by status")

    # lead
    lead_parser = subparsers.add_parser("lead", help="Show lead details")
    lead_parser.add_argument("--json", action="store_true", help="Output as JSON")
    lead_parser.add_argument("lead_id", type=int, help="Lead ID")

    # reply
    reply_parser = subparsers.add_parser("reply", help="Simulate reply (dry run)")
    reply_parser.add_argument("--json", action="store_true", help="Output as JSON")
    reply_parser.add_argument("lead_id", type=int, help="Lead ID")
    reply_parser.add_argument(
        "reply_type", choices=["positive", "neutral", "negative"], default="positive"
    )

    # config
    config_parser = subparsers.add_parser("config", help="Show/set config")
    config_parser.add_argument("--json", action="store_true", help="Output as JSON")
    config_parser.add_argument("key", nargs="?", help="Config key")
    config_parser.add_argument("value", nargs="?", help="Config value")

    # status
    status_parser = subparsers.add_parser("status", help="Show system status")
    status_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # enrich
    enrich_parser = subparsers.add_parser("enrich", help="Enrich a single lead with company data")
    enrich_parser.add_argument("--json", action="store_true", help="Output as JSON")
    enrich_parser.add_argument("lead_id", type=int, help="Lead ID")

    # enrich-all
    enrich_all_parser = subparsers.add_parser("enrich-all", help="Enrich multiple leads")
    enrich_all_parser.add_argument("--json", action="store_true", help="Output as JSON")
    enrich_all_parser.add_argument("--max", "-m", type=int, default=10, help="Max leads to enrich")

    # test
    test_parser = subparsers.add_parser("test", help="Run full test sequence")
    test_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # check-replies
    check_replies_parser = subparsers.add_parser(
        "check-replies", help="Check LinkedIn inbox for replies"
    )
    check_replies_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # set-company-url
    set_url_parser = subparsers.add_parser(
        "set-company-url", help="Set company URL for a lead (required for enrichment)"
    )
    set_url_parser.add_argument("--json", action="store_true", help="Output as JSON")
    set_url_parser.add_argument("lead_id", type=int, help="Lead ID")
    set_url_parser.add_argument("company_url", help="Company website URL")

    # help
    subparsers.add_parser("help", help="Show help")

    args = parser.parse_args()
    use_json = getattr(args, "json", False)

    # Set quiet mode if JSON output requested
    if use_json:
        set_quiet_mode(True)

    if not args.command or args.command == "help":
        show_help()
        return

    # Commands
    if args.command == "init":
        init_db()
        if use_json:
            from pathlib import Path

            db_path = str(Path(__file__).parent.parent.parent / "data" / "salesbud.db")
            print_json(True, 1, [{"db_path": db_path, "initialized": True}])
        else:
            logger.print_text("Database initialized!")

    elif args.command == "scrape":
        from salesbud.models.lead import get_all_leads

        count = scrape_leads(args.query, args.location, args.max)

        # Get all leads for JSON output
        all_leads = get_all_leads()

        if use_json:
            # Return leads as dicts with relevant fields
            data = [
                {
                    "id": l["id"],
                    "name": l.get("name"),
                    "headline": l.get("headline"),
                    "company": l.get("company"),
                    "location": l.get("location"),
                    "linkedin_url": l.get("linkedin_url"),
                    "status": l.get("status"),
                }
                for l in all_leads[:count]
            ]
            print_json(True, count, data)
        else:
            logger.print_text(f"\n✓ Scraped {count} leads")

    elif args.command == "connect":
        from salesbud.models.lead import get_all_leads

        run_connection_campaign(max_requests=args.max, delay_seconds=args.delay)

        # Get results
        all_leads = get_all_leads()
        connected = [l for l in all_leads if l.get("status") == "connection_requested"]

        if use_json:
            data = [
                {"lead_id": l["id"], "name": l.get("name"), "result": "sent"}
                for l in connected[: args.max]
            ]
            print_json(True, len(data), data)

    elif args.command == "check-connections":
        from salesbud.models.lead import get_leads_by_status

        check_pending_connections()

        pending = get_leads_by_status("connection_requested")

        if use_json:
            data = [
                {"lead_id": l["id"], "name": l.get("name"), "status": l.get("status")}
                for l in pending
            ]
            print_json(True, len(data), data)

    elif args.command == "sequence":
        from salesbud.models.lead import get_lead_by_id

        leads = get_leads_due_for_step(min_days=3)
        newly_connected_count = 0

        # This function handles both new and existing sequences internally
        run_sequence_step()

        # Get updated leads to report
        if use_json:
            data = []
            # Get newly connected leads that were started
            from salesbud.services.sequence import get_newly_connected_leads

            newly = get_newly_connected_leads()
            for lead in newly:
                data.append(
                    {"lead_id": lead["id"], "name": lead.get("name"), "step": 1, "sent": True}
                )

            # Get leads that had steps advanced
            leads = get_leads_due_for_step(min_days=3)
            for lead in leads:
                data.append(
                    {
                        "lead_id": lead["id"],
                        "name": lead.get("name"),
                        "step": lead.get("sequence_step", 0) + 1,
                        "sent": True,
                    }
                )

            print_json(True, len(data), data)

    elif args.command == "email":
        html = f"<div style='font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6;'>{args.body.replace(chr(10), '<br>')}</div>"
        success = send_email(args.to, args.subject, html, args.body)

        if use_json:
            data = [{"to": args.to, "subject": args.subject, "sent": success}]
            print_json(success, 1 if success else 0, data)
        else:
            if success:
                logger.print_text(
                    f"\n✓ Email {'logged (dry run)' if is_dry_run() else 'sent'} to {args.to}"
                )
            else:
                logger.print_text(f"\n✗ Failed to send email to {args.to}")
                sys.exit(EXIT_CODE_ERROR)

    elif args.command == "email-sequence":
        leads = get_leads_due_for_email(min_days=3)

        run_email_sequence_step()

        if use_json:
            new_starts = get_leads_ready_for_email_start()

            data = []
            for lead in new_starts:
                data.append(
                    {"lead_id": lead["id"], "name": lead.get("name"), "step": 1, "sent": True}
                )
            for lead in leads:
                data.append(
                    {
                        "lead_id": lead["id"],
                        "name": lead.get("name"),
                        "step": lead.get("email_sequence_step", 0) + 1,
                        "sent": True,
                    }
                )

            print_json(True, len(data), data)

    elif args.command == "add-email":
        from salesbud.models.lead import update_lead_email, get_lead_by_id

        lead = get_lead_by_id(args.lead_id)
        if not lead:
            if use_json:
                print_json(False, 0, [], [f"Lead {args.lead_id} not found"])
            else:
                logger.print_text(f"Lead {args.lead_id} not found.")
            sys.exit(EXIT_CODE_ERROR)
        else:
            update_lead_email(args.lead_id, args.email_address)
            if use_json:
                data = [
                    {"lead_id": args.lead_id, "email": args.email_address, "name": lead.get("name")}
                ]
                print_json(True, 1, data)
            else:
                logger.print_text(
                    f"✓ Set email for {lead.get('name', 'Unknown')} → {args.email_address}"
                )

    elif args.command == "find-email":
        from salesbud.models.lead import get_lead_by_id
        from salesbud.services.email_finder import (
            find_email_for_lead,
            verify_smtp,
            update_lead_email_with_verification,
        )

        lead = get_lead_by_id(args.lead_id)
        if not lead:
            if use_json:
                print_json(False, 0, [], [f"Lead {args.lead_id} not found"])
            else:
                logger.print_text(f"Lead {args.lead_id} not found.")
            sys.exit(EXIT_CODE_ERROR)

        email = find_email_for_lead(lead, quick_mode=args.quick)
        if email:
            verify_timeout = 3 if args.quick else 10
            verified = verify_smtp(email, timeout=verify_timeout)
            update_lead_email_with_verification(args.lead_id, email, "search", verified)
            if use_json:
                data = [{"lead_id": args.lead_id, "email": email, "verified": verified}]
                print_json(True, 1, data)
            else:
                logger.print_text(
                    f"✓ Found email for {lead.get('name', 'Unknown')}: {email} (verified: {verified})"
                )
        else:
            if use_json:
                print_json(False, 0, [], ["Could not find email for this lead"])
            else:
                logger.print_text(f"✗ Could not find email for {lead.get('name', 'Unknown')}")

    elif args.command == "find-emails":
        from salesbud.services.email_finder import batch_find_emails

        results = batch_find_emails(args.max, quick_mode=args.quick)
        if use_json:
            print_json(True, len(results), results)
        else:
            if results:
                logger.print_text(f"✓ Found {len(results)} emails:")
                for r in results:
                    logger.print_text(
                        f"  Lead {r['lead_id']}: {r['email']} (verified: {r['verified']})"
                    )
            else:
                logger.print_text("No emails found.")

    elif args.command == "workflow":
        logger.print_text("=== SalesBud Full Workflow ===\n")

        workflow_data = []

        # Step 1: Scrape
        logger.print_text("--- Step 1: Scraping Leads ---")
        count = scrape_leads(args.query, args.location, args.max_leads)
        logger.print_text(f"✓ Scraped {count} leads\n")

        from salesbud.models.lead import get_all_leads

        if use_json:
            workflow_data.append({"step": "scrape", "leads_added": count})

        # Step 2: Send Connection Requests
        logger.print_text("--- Step 2: Sending Connection Requests ---")
        run_connection_campaign(max_requests=args.max_connections, delay_seconds=60)
        logger.print_text("✓ Connection requests sent")

        if use_json:
            workflow_data.append({"step": "connect", "max_requests": args.max_connections})

        # Step 3: Check Connections (in real usage, you'd wait hours/days)
        if is_dry_run():
            logger.print_text("--- Step 3: Checking Connections (DRY RUN - simulating accepts) ---")
            from salesbud.models.lead import update_lead_status
            from salesbud.database import log_activity

            leads = get_all_leads()
            for lead in leads:
                if lead["status"] == "connection_requested":
                    update_lead_status(lead["id"], "connected")
                    log_activity(
                        lead["id"], "connection_accepted", f"Simulated accept for {lead['name']}"
                    )
            logger.print_text("✓ Simulated connection accepts\n")
            if use_json:
                workflow_data.append({"step": "check_connections", "simulated": True})
        else:
            logger.print_text("--- Step 3: Checking Connections ---")
            logger.print_text("(In production, you'd wait 24-48 hours for accepts)")
            check_pending_connections()
            logger.print_text("✓ Connection check complete")
            if use_json:
                workflow_data.append({"step": "check_connections", "simulated": False})

        # Step 4: Start DM Sequence for connected leads
        logger.print_text("--- Step 4: Starting DM Sequence ---")
        from salesbud.services.sequence import get_newly_connected_leads

        connected = get_newly_connected_leads()
        logger.print_text(f"Found {len(connected)} connected leads ready for DMs")
        for lead in connected[:5]:
            start_sequence_for_lead(lead["id"])
        logger.print_text("✓ Started DM sequences\n")

        if use_json:
            workflow_data.append({"step": "sequence_started", "count": len(connected[:5])})

        # Step 5: Run Email Sequence for leads with emails
        logger.print_text("--- Step 5: Running Email Sequence ---")
        run_email_sequence_step()
        logger.print_text("✓ Email sequence step complete\n")

        if use_json:
            workflow_data.append({"step": "email_sequence_complete", "complete": True})

        logger.print_text("=== Workflow Complete ===")
        logger.print_text("\nNext steps:")
        logger.print_text("  - Run 'uv run python -m salesbud sequence' to continue DM sequences")
        logger.print_text(
            "  - Run 'uv run python -m salesbud email-sequence' to continue email sequences"
        )
        logger.print_text(
            "  - Run 'uv run python -m salesbud add-email <id> <email>' to add emails to leads"
        )
        logger.print_text("  - Run 'uv run python -m salesbud dashboard' to monitor progress")

        if use_json:
            print_json(True, len(workflow_data), workflow_data)

    elif args.command == "dashboard":
        from salesbud.models.lead import get_lead_stats, get_all_leads

        stats = get_lead_stats()
        all_leads = get_all_leads()

        if not use_json:
            show_dashboard(args.status)

        if use_json:
            data = {
                "stats": stats,
                "leads": [
                    {
                        "id": l["id"],
                        "name": l.get("name"),
                        "company": l.get("company"),
                        "status": l.get("status"),
                        "sequence_step": l.get("sequence_step"),
                        "email_sequence_step": l.get("email_sequence_step"),
                        "has_email": bool(l.get("email")),
                    }
                    for l in all_leads
                ],
            }
            print_json(True, len(all_leads), [data])

    elif args.command == "lead":
        lead = show_lead_detail(args.lead_id)

        if use_json and lead:
            # Also get activities
            from salesbud.database import get_db

            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM activities WHERE lead_id = ? ORDER BY created_at DESC LIMIT 10",
                (args.lead_id,),
            )
            activities = [dict(row) for row in cursor.fetchall()]
            conn.close()

            data = {
                "id": lead["id"],
                "name": lead.get("name"),
                "headline": lead.get("headline"),
                "company": lead.get("company"),
                "location": lead.get("location"),
                "email": lead.get("email"),
                "status": lead.get("status"),
                "sequence_step": lead.get("sequence_step"),
                "email_sequence_step": lead.get("email_sequence_step"),
                "linkedin_url": lead.get("linkedin_url"),
                "activities": activities,
            }
            print_json(True, 1, [data])

    elif args.command == "reply":
        if is_dry_run():
            lead = simulate_reply(args.lead_id, args.reply_type)

            if use_json:
                from salesbud.models.lead import get_lead_by_id

                lead = get_lead_by_id(args.lead_id)
                new_status = "replied" if args.reply_type == "positive" else "paused"
                data = [
                    {
                        "lead_id": args.lead_id,
                        "reply_type": args.reply_type,
                        "new_status": new_status,
                    }
                ]
                print_json(True, 1, data)
        else:
            if use_json:
                print_json(False, 0, [], ["Reply simulation only works in dry-run mode"])
            else:
                logger.print_text(
                    "Reply simulation only works in dry-run mode. Set dry_run=1 in config."
                )
            sys.exit(EXIT_CODE_ERROR)

    elif args.command == "config":
        if args.key and args.value:
            set_config(args.key, args.value)
            if use_json:
                data = [{args.key: args.value}]
                print_json(True, 1, data)
            else:
                logger.print_text(f"Set {args.key} = {args.value}")
        elif args.key:
            val = get_config(args.key)
            if use_json:
                data = [{args.key: val}]
                print_json(True, 1, data)
            else:
                logger.print_text(f"{args.key} = {val}")
        else:
            # Get all config
            config_keys = [
                "dry_run",
                "dms_per_hour",
                "dms_per_day",
                "delay_minutes",
                "delay_variance",
                "emails_per_hour",
                "emails_per_day",
                "email_delay_minutes",
            ]
            config_data = {k: get_config(k) for k in config_keys}
            if use_json:
                print_json(True, len(config_data), [config_data])
            else:
                logger.print_text("Config:")
                logger.print_text("  LinkedIn:")
                for key in [
                    "dry_run",
                    "dms_per_hour",
                    "dms_per_day",
                    "delay_minutes",
                    "delay_variance",
                ]:
                    logger.print_text(f"    {key} = {get_config(key)}")
                logger.print_text("  Email:")
                for key in ["emails_per_hour", "emails_per_day", "email_delay_minutes"]:
                    logger.print_text(f"    {key} = {get_config(key)}")

    elif args.command == "status":
        from salesbud.models.lead import get_lead_stats, get_all_leads

        stats = get_lead_stats()
        all_leads = get_all_leads()

        # Get DM queue count
        dm_queue = len(get_leads_due_for_step(min_days=3))
        email_queue = len(get_leads_due_for_email(min_days=3))

        # Get LinkedIn auth status
        import os

        linkedin_session = os.getenv("LINKEDIN_SESSION_COOKIE")
        linkedin_auth = "cookie" if linkedin_session else "not_set"

        # Get Resend key status
        resend_key = os.getenv("RESEND_API_KEY")
        resend_key_set = bool(resend_key)

        # Get all config
        config_keys = [
            "dry_run",
            "dms_per_hour",
            "dms_per_day",
            "delay_minutes",
            "delay_variance",
            "emails_per_hour",
            "emails_per_day",
            "email_delay_minutes",
        ]
        config_data = {k: get_config(k) for k in config_keys}

        if use_json:
            from pathlib import Path

            db_path = str(Path(__file__).parent.parent.parent / "data" / "salesbud.db")
            data = {
                "dry_run": is_dry_run(),
                "db_ok": True,
                "db_path": db_path,
                "total_leads": stats.get("total", 0),
                "dm_queue": dm_queue,
                "email_queue": email_queue,
                "linkedin_auth": linkedin_auth,
                "resend_key_set": resend_key_set,
                "config": config_data,
            }
            print_json(True, 1, [data])
        else:
            logger.print_text("SalesBud Status")
            logger.print_text(f"  Mode: {'DRY RUN' if is_dry_run() else 'PRODUCTION'}")
            from pathlib import Path

            db_path = str(Path(__file__).parent.parent.parent / "data" / "salesbud.db")
            logger.print_text(f"  DB: {db_path} (OK)")
            logger.print_text(f"  Leads: {stats.get('total', 0)} total")
            logger.print_text(f"  DM queue: {dm_queue} due for next step")
            logger.print_text(f"  Email queue: {email_queue} due for next step")
            logger.print_text(
                f"  Config: dms_per_hour={config_data.get('dms_per_hour')}, emails_per_hour={config_data.get('emails_per_hour')}"
            )
            logger.print_text(
                f"  LinkedIn: session cookie {'SET' if linkedin_session else 'NOT SET'}"
            )
            logger.print_text(f"  Resend: API key {'SET' if resend_key_set else 'NOT SET'}")

    elif args.command == "test":
        logger.print_text("=== Running Test Sequence ===\n")
        init_db()
        logger.print_text("\n--- Step 1: Scrape ---")
        count = scrape_leads("CEO", "Austin, TX", 5)
        logger.print_text(f"Added {count} leads")
        logger.print_text("\n--- Step 2: Dashboard ---")
        show_dashboard()
        logger.print_text("\n--- Step 3: Lead Detail ---")
        show_lead_detail(1)
        logger.print_text("\n--- Step 4: Simulate Reply ---")
        simulate_reply(1, "positive")
        logger.print_text("\n=== Test Complete ===")

    elif args.command == "enrich":
        from salesbud.models.lead import get_lead_by_id
        from salesbud.services.enricher import enrich_lead as enrich_lead_data

        lead = get_lead_by_id(args.lead_id)
        if not lead:
            if use_json:
                print_json(False, 0, [], [f"Lead {args.lead_id} not found"])
            else:
                logger.print_text(f"Lead {args.lead_id} not found.")
            sys.exit(EXIT_CODE_ERROR)

        if not lead.get("company_url"):
            if use_json:
                print_json(False, 0, [], [f"Lead {args.lead_id} has no company_url"])
            else:
                logger.print_text(f"Lead {args.lead_id} has no company_url. Set it first.")
            sys.exit(EXIT_CODE_ERROR)

        success = enrich_lead_data(args.lead_id)

        if success:
            updated_lead = get_lead_by_id(args.lead_id)
            if use_json:
                data = [
                    {
                        "lead_id": args.lead_id,
                        "name": lead.get("name") if lead else None,
                        "company": lead.get("company") if lead else None,
                        "company_url": lead.get("company_url") if lead else None,
                        "company_description": updated_lead.get("company_description")
                        if updated_lead
                        else None,
                        "company_size_est": updated_lead.get("company_size_est")
                        if updated_lead
                        else None,
                        "buying_signals": updated_lead.get("buying_signals")
                        if updated_lead
                        else None,
                        "enriched_at": updated_lead.get("enriched_at") if updated_lead else None,
                    }
                ]
                print_json(True, 1, data)
            else:
                logger.print_text(
                    f"✓ Enriched lead {args.lead_id}: {lead.get('name') if lead else 'Unknown'}"
                )
                logger.print_text(
                    f"  Description: {updated_lead.get('company_description', 'N/A') if updated_lead else 'N/A'}"
                )
                logger.print_text(
                    f"  Size: {updated_lead.get('company_size_est', 'N/A') if updated_lead else 'N/A'}"
                )
                logger.print_text(
                    f"  Signals: {updated_lead.get('buying_signals', 'N/A') if updated_lead else 'N/A'}"
                )
        else:
            if use_json:
                print_json(False, 0, [], ["Enrichment failed"])
            else:
                logger.print_text(f"✗ Failed to enrich lead {args.lead_id}")

    elif args.command == "enrich-all":
        from salesbud.services.enricher import batch_enrich_leads

        results = batch_enrich_leads(args.max)

        enriched_count = sum(1 for r in results if r.get("enriched"))

        if use_json:
            data = [{"total": len(results), "enriched": enriched_count, "results": results}]
            print_json(True, len(results), [data])
        else:
            logger.print_text(f"Enriched {enriched_count}/{len(results)} leads")

    elif args.command == "check-replies":
        from salesbud.services.inbox import check_linkedin_inbox

        replies = check_linkedin_inbox()

        if use_json:
            print_json(True, len(replies), replies)

    elif args.command == "set-company-url":
        from salesbud.models.lead import update_lead_company_url, get_lead_by_id

        lead = get_lead_by_id(args.lead_id)
        if not lead:
            if use_json:
                print_json(False, 0, [], [f"Lead {args.lead_id} not found"])
            else:
                logger.print_text(f"Lead {args.lead_id} not found.")
            sys.exit(EXIT_CODE_ERROR)

        url = args.company_url.strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        update_lead_company_url(args.lead_id, url)

        if use_json:
            data = [{"lead_id": args.lead_id, "company_url": url, "name": lead.get("name")}]
            print_json(True, 1, data)
        else:
            logger.print_text(f"✓ Set company URL for {lead.get('name', 'Unknown')} → {url}")


if __name__ == "__main__":
    main()
