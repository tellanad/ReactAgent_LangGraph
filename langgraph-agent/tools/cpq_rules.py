"""Tool: CPQ pricing rules lookup."""
from langchain_core.tools import tool


MOCK_RULES = {
    "enterprise-suite": {
        "product": "Enterprise Suite",
        "base_price": 25000,
        "max_discount": 0.15,
        "approval_threshold": 10000,
        "bundle_options": ["Support Add-on", "Training Package", "Custom Integration"],
        "required_approvals": ["Sales Manager"],
        "checklist": [
            "Verify customer tier (Gold/Platinum)",
            "Check existing contract terms",
            "Validate bundle compatibility",
            "Confirm discount within threshold (max 15%)",
            "Get Sales Manager approval if > $10,000",
            "Attach signed SOW",
        ],
    },
    "starter-plan": {
        "product": "Starter Plan",
        "base_price": 500,
        "max_discount": 0.10,
        "approval_threshold": 5000,
        "bundle_options": ["Basic Support"],
        "required_approvals": [],
        "checklist": [
            "Verify customer email",
            "Confirm billing cycle (monthly/annual)",
            "Apply standard discount if applicable (max 10%)",
            "Generate invoice",
        ],
    },
}


@tool
def cpq_rules_lookup(product: str) -> dict:
    """Look up CPQ pricing rules and checklist for a product."""
    key = product.lower().replace(" ", "-")
    rules = MOCK_RULES.get(key)
    if not rules:
        return {"error": f"No CPQ rules for '{product}'", "available": list(MOCK_RULES.keys())}
    return rules