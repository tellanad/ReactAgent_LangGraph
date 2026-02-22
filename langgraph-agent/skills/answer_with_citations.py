"""
Skill 3: Answer with Citations
Uses retrieved chunks + RAG prompt to generate a grounded answer.
Refuses if confidence is low.
"""
from __future__ import annotations
from langchain_core.messages import HumanMessage, SystemMessage
from state import AgentState
from llm_selector import get_llm, estimate_cost
from prompts.registry import prompt_registry


def answer_with_citations(state: AgentState) -> dict:
    """Generate a grounded answer using retrieved chunks.
    
    Reads: messages, retrieved_chunks, llm_tier
    Sets: final_answer, citations
    Appends to: trace_log, total_cost
    """
    messages = state.get("messages", [])
    chunks = state.get("retrieved_chunks", [])
    tier = state.get("llm_tier", 1)

    if not messages:
        return {"final_answer": "No question provided.", "error": "No messages"}

    question = messages[-1].content if hasattr(messages[-1], "content") else str(messages[-1])

    # If no chunks were found, refuse gracefully
    if not chunks:
        return {
            "final_answer": "I don't have enough information to answer this question. No relevant documents were found.",
            "current_node": "answer_with_citations",
        }

    # Format chunks for the prompt
    chunks_text = "\n\n".join(
        f"{c.get('marker', '[?]')} {c['text']}\n   Source: {c['source']}"
        for c in chunks
    )

    # Build prompt
    system_prompt = prompt_registry.render(
        "rag_answer", "v1",
        retrieved_chunks=chunks_text,
        citation_instruction="Include citation markers like [1], [2] when referencing sources",
        question=question,
    )

    # Use the tier selected by the router
    llm = get_llm(tier=tier)
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=question),
    ])

    # Calculate cost
    usage = getattr(response, "usage_metadata", {})
    input_tokens = usage.get("input_tokens", 100)
    output_tokens = usage.get("output_tokens", 80)
    step_cost = estimate_cost(tier, input_tokens, output_tokens)

    trace_entry = {
        "node": "answer_with_citations",
        "model": f"tier_{tier}",
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost": step_cost,
        "chunks_used": len(chunks),
    }

    prev_cost = state.get("total_cost", 0.0)
    prev_trace = state.get("trace_log", [])
    existing_citations = state.get("citations", [])

    return {
        "final_answer": response.content,
        "citations": existing_citations,
        "total_cost": prev_cost + step_cost,
        "trace_log": prev_trace + [trace_entry],
        "current_node": "answer_with_citations",
    }