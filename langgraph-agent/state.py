# state.py
"""
Enterprise Ops Copilot — Agent State
Central TypedDict that flows through every LangGraph node.
"""
from __future__ import annotations
from typing import Any, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage


class AgentState(TypedDict, total=False):
    """Shared state for the Enterprise Ops Copilot graph."""

    # ── Conversation ────────────────────────────────────────────
    messages: list[BaseMessage]

    # ── Routing decisions (set by router skill) ─────────────────
    intent: str                        # qa | action | multi_step | summarize | compliance
    required_tools: list[str]          # tool names the router selected
    llm_tier: int                      # 0, 1, or 2
    risk_level: str                    # low | medium | high | critical

    # ── Budget tracking ─────────────────────────────────────────
    budget_remaining: float            # USD remaining for this run
    total_cost: float                  # USD spent so far
    token_usage: dict[str, int]        # {"input": N, "output": M}

    # ── Retrieval ───────────────────────────────────────────────
    retrieved_chunks: list[dict[str, Any]]   # [{text, source, score}]
    citations: list[str]                     # formatted citation strings

    # ── Output ──────────────────────────────────────────────────
    final_answer: str
    action_result: dict[str, Any]      # result from tool execution
    compliance_result: dict[str, Any]  # {risk_level, recommendation, escalation_needed}

    # ── Observability ───────────────────────────────────────────
    trace_log: list[dict[str, Any]]    # [{node, timestamp, model, tokens, cost}]
    current_node: str                  # which node is executing