"""
Skill 2: Retrieval
Calls search tools and formats results with citation markers.
No LLM call here — just tool execution and formatting.
"""
from __future__ import annotations
from state import AgentState
from tools import TOOL_MAP


def retrieve(state: AgentState) -> dict:
    """Execute retrieval based on router's tool selection.
    
    Reads: messages, required_tools
    Sets: retrieved_chunks, citations
    Appends to: trace_log
    """
    messages = state.get("messages", [])
    required_tools = state.get("required_tools", [])

    if not messages:
        return {"error": "No messages for retrieval"}

    # Extract query from last user message
    query = messages[-1].content if hasattr(messages[-1], "content") else str(messages[-1])

    chunks = []
    citations = []

    # Run search_docs if selected by router
    if "search_docs" in required_tools and "search_docs" in TOOL_MAP:
        search_tool = TOOL_MAP["search_docs"]
        results = search_tool.invoke({"query": query})

        # Handle both list and string returns
        if isinstance(results, list):
            for i, doc in enumerate(results):
                marker = f"[{i + 1}]"
                chunks.append({
                    "id": doc.get("id", f"chunk-{i}"),
                    "text": doc.get("text", ""),
                    "source": doc.get("source", "Unknown"),
                    "score": doc.get("score", 0.0),
                    "marker": marker,
                })
                citations.append(f"{marker} {doc.get('source', 'Unknown')}")

    # Run salesforce_lookup if selected
    if "salesforce_lookup" in required_tools and "salesforce_lookup" in TOOL_MAP:
        # Extract case ID from query (simple pattern match)
        case_id = _extract_case_id(query)
        if case_id:
            sf_tool = TOOL_MAP["salesforce_lookup"]
            result = sf_tool.invoke({"case_id": case_id})
            if "error" not in result:
                chunks.append({
                    "id": result.get("id", "sf-case"),
                    "text": str(result),
                    "source": f"Salesforce Case {case_id}",
                    "score": 1.0,
                    "marker": f"[SF-{case_id}]",
                })
                citations.append(f"[SF-{case_id}] Salesforce Case {case_id}")

    # Run cpq_rules if selected
    if "cpq_rules_lookup" in required_tools and "cpq_rules_lookup" in TOOL_MAP:
        product = _extract_product(query)
        if product:
            cpq_tool = TOOL_MAP["cpq_rules_lookup"]
            result = cpq_tool.invoke({"product": product})
            if "error" not in result:
                chunks.append({
                    "id": f"cpq-{product}",
                    "text": str(result),
                    "source": f"CPQ Rules: {product}",
                    "score": 1.0,
                    "marker": f"[CPQ]",
                })
                citations.append(f"[CPQ] CPQ Rules: {product}")

    trace_entry = {
        "node": "retrieve",
        "tools_called": [t for t in required_tools if t in TOOL_MAP],
        "chunks_found": len(chunks),
        "cost": 0.0,  # No LLM call in retrieval
    }

    prev_trace = state.get("trace_log", [])

    return {
        "retrieved_chunks": chunks,
        "citations": citations,
        "trace_log": prev_trace + [trace_entry],
        "current_node": "retrieve",
    }


def _extract_case_id(query: str) -> str | None:
    """Simple extraction of CASE-XXX pattern from query."""
    import re
    match = re.search(r"CASE-\d+", query, re.IGNORECASE)
    return match.group(0).upper() if match else None


def _extract_product(query: str) -> str | None:
    """Simple extraction of known product names from query."""
    query_lower = query.lower()
    products = ["enterprise suite", "starter plan"]
    for p in products:
        if p in query_lower:
            return p
    # Fallback: look for "product X" pattern
    import re
    match = re.search(r"product\s+(\w+)", query_lower)
    return match.group(1) if match else None