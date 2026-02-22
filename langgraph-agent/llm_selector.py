"""
Enterprise Ops Copilot — Tiered LLM Selector
Returns the right model based on tier (0/1/2).
When MOCK_LLM=true, returns a fake LLM that gives pre-built responses.
"""
from __future__ import annotations
from typing import Any
from config import (
    MOCK_LLM,
    TIER_MODELS,
    TIER_TEMPERATURES,
    TIER_MAX_TOKENS,
    COST_PER_1K,
)


def get_llm(tier: int = 0):
    """Factory: returns an LLM instance based on tier.
    
    Tier 0: cheap  — routing, extraction, summarization
    Tier 1: mid    — grounded Q&A with citations
    Tier 2: strong — compliance, multi-hop reasoning
    """
    if tier not in TIER_MODELS:
        raise ValueError(f"Invalid tier: {tier}. Must be 0, 1, or 2.")

    if MOCK_LLM:
        return MockLLM(tier=tier)

    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=TIER_MODELS[tier],
        temperature=TIER_TEMPERATURES[tier],
        max_tokens=TIER_MAX_TOKENS[tier],
    )


def estimate_cost(tier: int, input_tokens: int, output_tokens: int) -> float:
    """Estimate USD cost for a given tier and token counts."""
    model = TIER_MODELS[tier]
    rates = COST_PER_1K.get(model, {"input": 0, "output": 0})
    cost = (input_tokens / 1000) * rates["input"] + (output_tokens / 1000) * rates["output"]
    return round(cost, 6)


# ── Mock LLM (used when MOCK_LLM=true) ──────────────────────────

class MockLLM:
    """Fake LLM for testing without API keys."""

    def __init__(self, tier: int = 0):
        self.tier = tier
        self.model = TIER_MODELS[tier]

    def invoke(self, messages: list, **kwargs) -> "MockResponse":
        """Simulate an LLM call."""
        last_msg = messages[-1] if messages else None
        content = self._generate_response(last_msg)
        return MockResponse(content=content, model=self.model)

    async def ainvoke(self, messages: list, **kwargs) -> "MockResponse":
        """Async version."""
        return self.invoke(messages, **kwargs)

    def bind_tools(self, tools: list) -> "MockLLM":
        """Mock tool binding — returns self."""
        self._tools = tools
        return self

    def _generate_response(self, last_msg) -> str:
        """Generate a mock response based on tier and message content."""
        text = ""
        if last_msg:
            text = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
        text_lower = text.lower()

        if self.tier == 0:
            if any(w in text_lower for w in ["calculate", "+", "-", "*", "/", "how much"]):
                return '{"intent": "action", "required_tools": ["calculator"], "llm_tier": 0, "risk_level": "low", "reasoning": "Math calculation requested"}'
            elif any(w in text_lower for w in ["ticket", "jira", "create", "open"]):
                return '{"intent": "action", "required_tools": ["create_jira_ticket"], "llm_tier": 0, "risk_level": "low", "reasoning": "Action requested — ticket creation"}'
            elif any(w in text_lower for w in ["compliant", "compliance", "hipaa", "medical", "legal"]):
                return '{"intent": "compliance", "required_tools": ["search_docs"], "llm_tier": 2, "risk_level": "high", "reasoning": "Compliance/risk assessment needed"}'
            elif any(w in text_lower for w in ["summarize", "summary", "tldr", "shorten"]):
                return '{"intent": "summarize", "required_tools": [], "llm_tier": 0, "risk_level": "low", "reasoning": "Summarization requested"}'
            elif any(w in text_lower for w in ["cpq", "quote", "pricing", "checklist"]):
                return '{"intent": "action", "required_tools": ["cpq_rules_lookup"], "llm_tier": 0, "risk_level": "low", "reasoning": "CPQ lookup requested"}'
            elif any(w in text_lower for w in ["case-", "salesforce", "case id"]):
                return '{"intent": "qa", "required_tools": ["salesforce_lookup", "search_docs"], "llm_tier": 1, "risk_level": "low", "reasoning": "Case lookup needed"}'
            else:
                return '{"intent": "qa", "required_tools": ["search_docs"], "llm_tier": 1, "risk_level": "low", "reasoning": "Standard knowledge query"}'

        elif self.tier == 1:
            return "Based on the retrieved documents, the refund policy allows full refunds within 30 days for standard products. [Source: Policy Manual v4.2, Section 3.1]"

        elif self.tier == 2:
            return '{"status": "needs_review", "recommendation": "This request involves PHI data. Route to compliance team for human review.", "escalation_needed": true, "cited_policies": ["Compliance Framework v3.0, Section 2.4"]}'

        return "Mock response"


class MockResponse:
    """Mimics LangChain AIMessage interface."""

    def __init__(self, content: str, model: str):
        self.content = content
        self.model = model
        self.tool_calls = []
        self.usage_metadata = {"input_tokens": 50, "output_tokens": 30}

    def __str__(self):
        return self.content