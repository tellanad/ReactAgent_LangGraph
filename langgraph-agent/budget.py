# budget.py
"""
Enterprise Ops Copilot — Budget Guard
Checks remaining budget before LLM calls.
Can downgrade tier or stop execution if budget is exhausted.
"""
from __future__ import annotations
from state import AgentState
from config import MAX_BUDGET_PER_RUN, BUDGET_WARNING_PCT, GRACEFUL_DEGRADE


def budget_guard(state: AgentState) -> dict:
    """Check budget before proceeding to skill execution.
    
    Reads: total_cost, llm_tier
    May modify: llm_tier (downgrade), budget_remaining
    Sets: error (if budget exhausted)
    Appends to: trace_log
    """
    total_cost = state.get("total_cost", 0.0)
    current_tier = state.get("llm_tier", 0)
    budget_remaining = MAX_BUDGET_PER_RUN - total_cost

    trace_entry = {
        "node": "budget_guard",
        "total_cost": total_cost,
        "budget_remaining": budget_remaining,
        "original_tier": current_tier,
        "cost": 0.0,
    }

    result = {
        "budget_remaining": budget_remaining,
        "current_node": "budget_guard",
    }

    # Budget exhausted — stop
    if budget_remaining <= 0:
        result["final_answer"] = (
            f"Budget exhausted (${total_cost:.4f} / ${MAX_BUDGET_PER_RUN:.2f}). "
            "Cannot continue processing. Please start a new session or increase budget."
        )
        result["error"] = "budget_exhausted"
        trace_entry["action"] = "blocked"
        prev_trace = state.get("trace_log", [])
        result["trace_log"] = prev_trace + [trace_entry]
        return result

    # Budget warning — downgrade if enabled
    used_pct = total_cost / MAX_BUDGET_PER_RUN
    if used_pct >= BUDGET_WARNING_PCT and GRACEFUL_DEGRADE and current_tier > 0:
        new_tier = max(0, current_tier - 1)
        result["llm_tier"] = new_tier
        trace_entry["action"] = f"downgraded_tier_{current_tier}_to_{new_tier}"
        trace_entry["reason"] = f"Budget {used_pct:.0%} used, degrading to save cost"
    else:
        trace_entry["action"] = "passed"

    prev_trace = state.get("trace_log", [])
    result["trace_log"] = prev_trace + [trace_entry]
    return result


def should_stop_for_budget(state: AgentState) -> str:
    """Conditional edge function: check if budget guard blocked execution.
    
    Returns:
        "blocked" — budget exhausted, go to final response
        "continue" — budget OK, proceed to skill
    """
    if state.get("error") == "budget_exhausted":
        return "blocked"
    return "continue"