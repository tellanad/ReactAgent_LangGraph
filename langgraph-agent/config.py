# config.py
"""
Enterprise Ops Copilot — Configuration
Central config for model tiers, cost tables, budget limits, and mock mode.
"""

import os
from dotenv import load_dotenv

load_dotenv()


MOCK_LLM = os.getenv("MOCK_LLM", "true").lower() == "true"


#__LLMTIER_CONFIG____________________________________________
TIER_MODELS = {
    0: os.getenv("TIER0_MODEL", "gpt-4o-mini"),   # routing, extraction, summarization
    1: os.getenv("TIER1_MODEL", "gpt-4o"),         # grounded Q&A with citations
    2: os.getenv("TIER2_MODEL", "gpt-4o"),         # compliance, multi-hop reasoning
}

TIER_TEMPERATURES = {0: 0.0, 1: 0.2, 2: 0.3}
TIER_MAX_TOKENS   = {0: 512, 1: 2048, 2: 4096}



# ── Cost per 1K Tokens (USD) ────────────────────────────────────
COST_PER_1K = {
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4o":      {"input": 0.0025,  "output": 0.01},
}

# ── Budget Defaults ─────────────────────────────────────────────
MAX_BUDGET_PER_RUN  = float(os.getenv("MAX_BUDGET_PER_RUN", "0.50"))
BUDGET_WARNING_PCT  = 0.80    # warn at 80% usage
GRACEFUL_DEGRADE    = True    # drop to cheaper tier if budget tight


# ── Intent Categories ───────────────────────────────────────────
INTENTS = ["qa", "action", "multi_step", "summarize", "compliance"]


# ── Risk Levels ─────────────────────────────────────────────────
RISK_LEVELS = ["low", "medium", "high", "critical"]


# ── Service URLs ────────────────────────────────────────────────
NESTJS_BACKEND_URL = os.getenv("NESTJS_BACKEND_URL", "http://localhost:3000")

# ── Tool Registry (available tools) ─────────────────────────────
AVAILABLE_TOOLS = [
    "search_docs",
    "salesforce_lookup",
    "cpq_rules_lookup",
    "create_jira_ticket",
    "calculator",
]


