"""
Skill 5: Compliance / Risk Check
Uses Tier 2 (strongest) LLM for high-risk reasoning.
Stricter prompt, explicit refusal/escalation logic.
If uncertain, always escalates to human review.
"""
from __future__ import annotations
import json
from langchain_core.messages import HumanMessage, SystemMessage
from state import AgentState
from llm_selector import get_llm, estimate_cost
from prompts.registry import prompt_registry


def compliance_check(state: AgentState) -> dict:
    """Assess compliance risk and recommend action.
    
    Reads: messages, retrieved_chunks, risk_level
    Sets: final_answer, compliance_result
    Appends to: trace_log, total_cost
    """
    messages = state.get("messages", [])
    chunks = state.get("retrieved_chunks", [])
    risk_level = state.get("risk_level", "high")

    if not messages:
        return {"final_answer": "No request to assess.", "error": "No messages"}

    question = messages[-1].content if hasattr(messages[-1], "content") else str(messages[-1])

    # Build policy context from retrieved chunks
    if chunks:
        policy_context = "\n\n".join(
            f"[{c.get('marker', '?')}] {c['text']}\n   Source: {c['source']}"
            for c in chunks
        )
    else:
        policy_context = "No policy documents retrieved. Exercise maximum caution."

    # Always use Tier 2 for compliance — strongest model
    system_prompt = prompt_registry.render(
        "compliance", "v1",
        policy_context=policy_context,
        risk_level=risk_level,
        question=question,
    )

    llm = get_llm(tier=2)
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=question),
    ])

    # Parse compliance result
    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        # If LLM doesn't return JSON, default to escalation (safe side)
        result = {
            "status": "needs_review",
            "recommendation": "Could not parse compliance assessment. Escalating to human reviewer.",
            "cited_policies": [],
            "escalation_needed": True,
            "confidence": 0.0,
        }

    # Force escalation if risk is critical or confidence is low
    confidence = result.get("confidence", 0.0)
    if risk_level == "critical" or confidence < 0.7:
        result["escalation_needed"] = True
        if confidence < 0.7:
            result["recommendation"] = (
                f"{result.get('recommendation', '')} "
                "[AUTO-FLAG: Low confidence ({:.0%}). Escalated to human review.]".format(confidence)
            )

    # Build human-readable answer
    final_answer = _format_compliance_answer(result, question)

    # Cost tracking — Tier 2 is expensive
    usage = getattr(response, "usage_metadata", {})
    input_tokens = usage.get("input_tokens", 200)
    output_tokens = usage.get("output_tokens", 150)
    step_cost = estimate_cost(2, input_tokens, output_tokens)

    trace_entry = {
        "node": "compliance_check",
        "model": "tier_2",
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost": step_cost,
        "risk_level": risk_level,
        "escalation": result.get("escalation_needed", False),
    }

    prev_cost = state.get("total_cost", 0.0)
    prev_trace = state.get("trace_log", [])

    return {
        "final_answer": final_answer,
        "compliance_result": result,
        "total_cost": prev_cost + step_cost,
        "trace_log": prev_trace + [trace_entry],
        "current_node": "compliance_check",
    }


def _format_compliance_answer(result: dict, question: str) -> str:
    """Format compliance result into a readable response."""
    status = result.get("status", "unknown")
    recommendation = result.get("recommendation", "No recommendation available.")
    policies = result.get("cited_policies", [])
    escalation = result.get("escalation_needed", False)
    confidence = result.get("confidence", 0.0)

    # Status emoji/label
    status_labels = {
        "compliant": "COMPLIANT",
        "non_compliant": "NON-COMPLIANT",
        "needs_review": "NEEDS HUMAN REVIEW",
    }
    status_label = status_labels.get(status, status.upper())

    lines = [
        f"Compliance Assessment: {status_label}",
        f"Confidence: {confidence:.0%}",
        "",
        f"Recommendation: {recommendation}",
    ]

    if policies:
        lines.append("")
        lines.append("Cited Policies:")
        for policy in policies:
            lines.append(f"  - {policy}")

    if escalation:
        lines.append("")
        lines.append(">> ESCALATION REQUIRED: This request has been flagged for human review.")

    return "\n".join(lines)