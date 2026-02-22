"""Tool: Salesforce case lookup."""
from langchain_core.tools import tool


MOCK_CASES = {
    "CASE-001": {
        "id": "CASE-001",
        "subject": "Product delivery delayed - Enterprise license",
        "status": "Open",
        "priority": "High",
        "customer": "Acme Corp",
        "contact_email": "john@acme.com",
        "description": "Customer reports 2-week delay on enterprise license delivery. Affecting 500+ users.",
        "history": [
            {"date": "2026-02-18", "action": "Created by support agent"},
            {"date": "2026-02-19", "action": "Escalated to operations"},
            {"date": "2026-02-20", "action": "Vendor contacted for ETA"},
        ],
    },
    "CASE-002": {
        "id": "CASE-002",
        "subject": "Billing discrepancy - Invoice #4521",
        "status": "Pending",
        "priority": "Medium",
        "customer": "TechStart Inc",
        "contact_email": "billing@techstart.io",
        "description": "Invoice shows $15,000 but agreed price was $12,000. Needs CPQ verification.",
        "history": [
            {"date": "2026-02-20", "action": "Created by customer via portal"},
            {"date": "2026-02-21", "action": "Assigned to billing team"},
        ],
    },
}


@tool
def salesforce_lookup(case_id: str) -> dict:
    """Look up a Salesforce case by ID. Returns case details, history, and customer info."""
    case = MOCK_CASES.get(case_id)
    if not case:
        return {"error": f"Case '{case_id}' not found", "available": list(MOCK_CASES.keys())}
    return case