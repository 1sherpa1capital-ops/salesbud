from typing import Optional
from salesbud.utils import logger
from salesbud.models.lead import update_lead_personalization, get_lead_by_id

def generate_personalization(lead_id: int) -> Optional[str]:
    """
    Synthesizes the company_research and lead profile to generate a highly personalized icebreaker.
    Note: Currently uses a heuristic template. In a production AI setup, plug in OpenAI/Anthropic/GenKit here.
    """
    lead = get_lead_by_id(lead_id)
    if not lead:
        logger.print_text(f"Lead {lead_id} not found.")
        return None
        
    research = lead.get("company_research")
    if not research:
        logger.print_text(f"Lead {lead_id} lacks company_research. Run research first.")
        return None

    # In a full AI implementation, you would pass `research` to an LLM context window here.
    # For now, we simulate personalization using keyword extraction heuristics.
    # E.g., if we see "machine learning" in the snapshot, we bring it up.
    
    research_lower = research.lower()
    hook = ""
    if "ai" in research_lower or "artificial intelligence" in research_lower:
        hook = "noticed your team is heavily leaning into AI."
    elif "marketing" in research_lower:
        hook = "saw the impressive agency work your team is pushing out."
    elif "saas" in research_lower or "software" in research_lower:
        hook = "loved the angle you're taking with your software platform."
    else:
        hook = "saw the incredible momentum your company has been building."

    # Construct the Icebreaker
    firstName = lead.get("name", "").split(" ")[0] if lead.get("name") else "there"
    title = lead.get("headline", "").split(" ")[0] if lead.get("headline") else "leader"
    
    icebreaker = f"Hey {firstName}, I was diving into what you're building and {hook} As a {title}, I'm sure you have a lot on your plate."
    
    update_lead_personalization(lead_id, icebreaker)
    logger.print_text(f"✓ Generated Icebreaker: '{icebreaker}'")
    
    return icebreaker
