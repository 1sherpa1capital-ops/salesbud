import subprocess
from typing import Optional
from salesbud.utils import logger
from salesbud.models.lead import update_lead_research, get_lead_by_id

def perform_company_research(lead_id: int) -> Optional[str]:
    """Runs agent-browser on the lead's company_url, captures snapshot, and saves to DB."""
    lead = get_lead_by_id(lead_id)
    if not lead:
        logger.print_text(f"Lead {lead_id} not found.")
        return None
        
    url = lead.get("company_url")
    if not url:
        logger.print_text(f"Lead {lead_id} is missing a company_url.")
        return None

    logger.print_text(f"Starting agent-browser research on: {url}")
    
    try:
        # Open URL
        subprocess.run(["agent-browser", "open", url], check=True, capture_output=True)
        
        # Wait for page to load completely
        subprocess.run(["agent-browser", "wait", "--load", "networkidle"], check=True, capture_output=True)
        
        # Take an interactive snapshot with clean text output (-C)
        result = subprocess.run(["agent-browser", "snapshot", "-i", "-C"], check=True, capture_output=True, text=True)
        research_data = result.stdout.strip()
        
        # Close the browser session
        subprocess.run(["agent-browser", "close"], check=False, capture_output=True)
        
        if not research_data:
            logger.print_text("Research yielded empty data.")
            return None
            
        update_lead_research(lead_id, research_data)
        logger.print_text(f"✓ Research successfully captured ({len(research_data)} chars).")
        return research_data
        
    except subprocess.CalledProcessError as e:
        logger.print_text(f"agent-browser failed: {e.stderr if e.stderr else str(e)}")
        # Make sure to close if it crashed
        subprocess.run(["agent-browser", "close"], check=False, capture_output=True)
        return None
    except FileNotFoundError:
        logger.print_text("agent-browser is not installed or not in PATH.")
        return None
