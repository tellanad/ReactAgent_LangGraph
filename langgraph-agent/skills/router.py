"""
Skill 1: Router
The brain of the agent. Uses Tier 0 (cheap) LLM to classify intent
and decide which tools, model tier, and skill to use.
"""
from __future__ import annotations
import json
from langchain_core.messages import HumanMessage, SystemMessage
from state import AgentState
from llm_selector import get_llm, estimate_cost
from prompts.registry import prompt_registry
from config import AVAILABLE_TOOLS


def route_intent(state: AgentState) -> dict:
    """Classify user intent and build execution plan.
    
    Sets: intent, required_tools, llm_tier, risk_level
    Appends to: trace_log, total_cost
    """
    messages = state.get("messages", [])
    if not messages:
        return {"error": "No messages to route"}

    # Get the last user message
    last_msg = messages[-1].content if hasattr(messages[-1], "content") else str(messages[-1])

    # Build the router prompt (Tier 0 — cheapest)
    system_prompt = prompt_registry.render(
        "router", "v1",
        user_role="support_agent",
        available_tools=", ".join(AVAILABLE_TOOLS),
    )

    llm = get_llm(tier=0)
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=last_msg),
    ])

    # Parse the JSON response
    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        # Fallback if LLM doesn't return valid JSON
        result = {
            "intent": "qa",
            "required_tools": ["search_docs"],
            "llm_tier": 1,
            "risk_level": "low",
            "reasoning": "Failed to parse router response, defaulting to Q&A",
        }

    # Calculate cost for this step
    usage = getattr(response, "usage_metadata", None) or {}
    input_tokens = usage.get("input_tokens", 50)
    output_tokens = usage.get("output_tokens", 30)
    step_cost = estimate_cost(0, input_tokens, output_tokens)

    # Build trace entry
    trace_entry = {
        "node": "route_intent",
        "model": "tier_0",
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost": step_cost,
        "result": result,
    }

    prev_cost = state.get("total_cost", 0.0)
    prev_trace = state.get("trace_log", [])

    return {
        "intent": result.get("intent", "qa"),
        "required_tools": result.get("required_tools", []),
        "llm_tier": result.get("llm_tier", 1),
        "risk_level": result.get("risk_level", "low"),
        "total_cost": prev_cost + step_cost,
        "trace_log": prev_trace + [trace_entry],
        "current_node": "route_intent",
    }