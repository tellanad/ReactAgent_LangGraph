"""
Skill 6: Summarizer
Cheap model, token-limited. Summarizes or rewrites content.
"""
from __future__ import annotations
from langchain_core.messages import HumanMessage, SystemMessage
from state import AgentState
from llm_selector import get_llm, estimate_cost
from prompts.registry import prompt_registry


def summarize(state: AgentState) -> dict:
    """Summarize content from messages or retrieved chunks.
    
    Reads: messages, retrieved_chunks (optional)
    Sets: final_answer
    Appends to: trace_log, total_cost
    """
    messages = state.get("messages", [])
    chunks = state.get("retrieved_chunks", [])

    if not messages:
        return {"final_answer": "Nothing to summarize.", "error": "No messages"}

    question = messages[-1].content if hasattr(messages[-1], "content") else str(messages[-1])

    # Determine what to summarize
    # If there are retrieved chunks, summarize those; otherwise summarize the user's input
    if chunks:
        content = "\n\n".join(c.get("text", "") for c in chunks)
    else:
        content = question

    # Build prompt — always Tier 0 (cheapest)
    system_prompt = prompt_registry.render(
        "summarize", "v1",
        format="bullet points",
        max_tokens="200",
        content=content,
    )

    llm = get_llm(tier=0)
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Summarize this:\n\n{content}"),
    ])

    # Cost
    # Calculate cost for this step
    usage = getattr(response, "usage_metadata", None) or {}
    input_tokens = usage.get("input_tokens", 50)
    output_tokens = usage.get("output_tokens", 30)
    step_cost = estimate_cost(0, input_tokens, output_tokens)

    trace_entry = {
        "node": "summarize",
        "model": "tier_0",
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost": step_cost,
        "content_length": len(content),
    }

    prev_cost = state.get("total_cost", 0.0)
    prev_trace = state.get("trace_log", [])

    return {
        "final_answer": response.content,
        "total_cost": prev_cost + step_cost,
        "trace_log": prev_trace + [trace_entry],
        "current_node": "summarize",
    }
