"""Tool: Search internal docs + knowledge base."""
from langchain_core.tools import tool


MOCK_DOCS = [
    {
        "id": "DOC-001",
        "text": "Refund Policy: Full refunds are available within 30 days of purchase for all standard products. Enterprise licenses require VP approval for refunds after the 15-day cooling period.",
        "source": "Policy Manual v4.2, Section 3.1",
        "score": 0.95,
    },
    {
        "id": "DOC-002",
        "text": "Escalation Matrix: Priority 1 (Critical) issues must be escalated to the on-call manager within 1 hour. Priority 2 (High) within 4 hours. All compliance-related queries go directly to the Legal team.",
        "source": "Ops Handbook, Chapter 7",
        "score": 0.88,
    },
    {
        "id": "DOC-003",
        "text": "CPQ Guidelines: All quotes above $10,000 require manager approval. Discounts exceeding 20% need VP sign-off. Product bundles must follow the approved combination matrix.",
        "source": "Sales Ops Guide v2.1, Section 5",
        "score": 0.91,
    },
    {
        "id": "DOC-004",
        "text": "HIPAA Compliance: Any request involving Protected Health Information (PHI) must be routed to the compliance team. AI-generated responses about medical data require human review before sending.",
        "source": "Compliance Framework v3.0, Section 2.4",
        "score": 0.97,
    },
    {
        "id": "DOC-005",
        "text": "SLA Definitions: Standard support: 24h response. Premium: 4h response, 8h resolution. Enterprise: 1h response, 4h resolution. Breach penalties apply per contract terms.",
        "source": "Service Agreements, Appendix A",
        "score": 0.85,
    },
]


@tool
def search_docs(query: str) -> list[dict]:
    """Search internal documents and knowledge base. Returns top matching chunks with citations."""
    query_lower = query.lower()
    scored = []
    for doc in MOCK_DOCS:
        relevance = sum(1 for word in query_lower.split() if word in doc["text"].lower())
        scored.append({**doc, "relevance": relevance})

    results = sorted(scored, key=lambda x: x["relevance"], reverse=True)[:3]
    # Remove the relevance key before returning
    return [{"id": r["id"], "text": r["text"], "source": r["source"], "score": r["score"]} for r in results]