"""Tool: Create Jira ticket."""
import random
from langchain_core.tools import tool


@tool
def create_jira_ticket(summary: str, description: str, priority: str = "Medium") -> dict:
    """Create a Jira ticket with the given summary, description, and priority."""
    ticket_id = f"OPS-{random.randint(1000, 9999)}"
    return {
        "ticket_id": ticket_id,
        "summary": summary,
        "description": description,
        "priority": priority,
        "status": "Open",
        "url": f"https://jira.ops.co/browse/{ticket_id}",
    }