# registry.py
"""
Enterprise Ops Copilot — Dynamic Prompt Registry
Versioned, parameterized prompt templates.
Each skill requests its prompt by name + version.
"""
from __future__ import annotations
from typing import Optional


# ── Prompt Template Store ────────────────────────────────────────

TEMPLATES = {

    "router:v1": {
        "name": "router",
        "version": "v1",
        "domain": "general",
        "risk_tier": 0,
        "template": """You are an intent classifier for an Enterprise Ops Copilot.

Classify the user request and determine the execution plan.

User role: {user_role}
Available tools: {available_tools}

Rules:
- "qa" = user wants information/answer
- "action" = user wants something done (create ticket, draft email, etc.)
- "multi_step" = user needs multiple tools chained together
- "summarize" = user wants content shortened/rewritten
- "compliance" = request involves legal, medical, or policy risk

Respond ONLY with valid JSON:
{{
  "intent": "qa|action|multi_step|summarize|compliance",
  "required_tools": ["tool1", "tool2"],
  "llm_tier": 0 or 1 or 2,
  "risk_level": "low|medium|high|critical",
  "reasoning": "one sentence explanation"
}}""",
    },

    "rag_answer:v1": {
        "name": "rag_answer",
        "version": "v1",
        "domain": "support",
        "risk_tier": 1,
        "template": """You are a grounded Q&A assistant for enterprise support.

RULES:
- Answer ONLY based on the provided context chunks below
- If the context is insufficient, say "I don't have enough information to answer this confidently"
- {citation_instruction}
- Be concise and direct

CONTEXT CHUNKS:
{retrieved_chunks}

USER QUESTION:
{question}""",
    },

    "action:v1": {
        "name": "action",
        "version": "v1",
        "domain": "operations",
        "risk_tier": 0,
        "template": """You are an action executor for enterprise operations.

Action requested: {action_type}
Available tools: {available_tools}

Parse the user request and determine:
1. Which tool to call
2. What parameters to pass
3. How to format the result for the user

Respond with JSON:
{{
  "tool": "tool_name",
  "params": {{}},
  "user_message": "what to tell the user"
}}""",
    },

    "compliance:v1": {
        "name": "compliance",
        "version": "v1",
        "domain": "legal",
        "risk_tier": 2,
        "template": """You are a compliance assessment specialist. BE EXTREMELY CAREFUL.

RULES:
- If medical, legal, or financial risk is HIGH or CRITICAL, recommend escalation
- Never provide definitive legal or medical advice
- Always cite policy sources
- If uncertain, err on the side of caution and ESCALATE

POLICY CONTEXT:
{policy_context}

RISK LEVEL: {risk_level}

USER REQUEST:
{question}

Respond with JSON:
{{
  "status": "compliant|non_compliant|needs_review",
  "recommendation": "what to do",
  "cited_policies": ["source1", "source2"],
  "escalation_needed": true or false,
  "confidence": 0.0 to 1.0
}}""",
    },

    "summarize:v1": {
        "name": "summarize",
        "version": "v1",
        "domain": "general",
        "risk_tier": 0,
        "template": """Summarize the following content.

Format: {format}
Max length: {max_tokens} tokens

Rules:
- Be precise, retain key facts, dates, and action items
- Do not add information not present in the source
- Use {format} format

CONTENT:
{content}""",
    },

}


# ── Registry Class ───────────────────────────────────────────────

class PromptRegistry:
    """Retrieves and renders prompt templates by name and version."""

    def __init__(self):
        self._templates = TEMPLATES.copy()

    def get(self, name: str, version: str = "v1") -> dict:
        """Get a raw template by name:version."""
        key = f"{name}:{version}"
        if key not in self._templates:
            raise KeyError(f"Prompt template '{key}' not found. Available: {list(self._templates.keys())}")
        return self._templates[key]

    def render(self, name: str, version: str = "v1", **params) -> str:
        """Get template and fill in parameters.
        
        Usage:
            registry = PromptRegistry()
            prompt = registry.render("router", "v1",
                user_role="support_agent",
                available_tools="search_docs, salesforce_lookup"
            )
        """
        template = self.get(name, version)
        rendered = template["template"]
        for key, value in params.items():
            rendered = rendered.replace(f"{{{key}}}", str(value))
        return rendered

    def list_templates(self) -> list[dict]:
        """List all available templates (metadata only, no template text)."""
        return [
            {"name": t["name"], "version": t["version"], "domain": t["domain"], "risk_tier": t["risk_tier"]}
            for t in self._templates.values()
        ]

    def register(self, key: str, template: dict) -> None:
        """Add or override a template at runtime."""
        self._templates[key] = template


# ── Singleton instance ───────────────────────────────────────────
prompt_registry = PromptRegistry()