# graph.py
"""
Enterprise Ops Copilot — LangGraph StateGraph
The main ReAct agent graph. Wires all skills together.

Flow:
  ingest → route_intent → budget_guard → [skill branch] → final_response

Branches (based on router output):
  qa         → retrieve → answer_with_citations → final
  action     → execute_action → final
  summarize  → summarize → final
  compliance → retrieve → compliance_check → final
  multi_step → retrieve → answer_with_citations → final (same as qa for now)
"""
from __future__ import annotations
from langgraph.graph import StateGraph, START, END
from state import AgentState
from skills.router import route_intent
from skills.retrieval import retrieve
from skills.answer_with_citations import answer_with_citations
from skills.action_executor import execute_action
from skills.compliance_check import compliance_check
from skills.summarizer import summarize
from budget import budget_guard, should_stop_for_budget
from config import MAX_BUDGET_PER_RUN


# ── Node: Ingest User Input ─────────────────────────────────────

def ingest_user(state: AgentState) -> dict:
    """Initialize state defaults for a new run."""
    return {
        "total_cost": state.get("total_cost", 0.0),
        "budget_remaining": MAX_BUDGET_PER_RUN - state.get("total_cost", 0.0),
        "trace_log": state.get("trace_log", []),
        "current_node": "ingest_user",
    }


# ── Node: Final Response ────────────────────────────────────────

def final_response(state: AgentState) -> dict:
    """Package the final response with metadata."""
    answer = state.get("final_answer", "I couldn't process your request.")
    citations = state.get("citations", [])
    total_cost = state.get("total_cost", 0.0)

    # Append citations to answer if present
    if citations:
        citation_block = "\n\nSources:\n" + "\n".join(f"  {c}" for c in citations)
        answer += citation_block

    return {
        "final_answer": answer,
        "current_node": "final_response",
    }


# ── Routing Functions ────────────────────────────────────────────

def route_by_intent(state: AgentState) -> str:
    """Conditional edge: route to the right skill based on intent."""
    intent = state.get("intent", "qa")

    if intent == "compliance":
        return "retrieve_for_compliance"
    elif intent == "action":
        return "execute_action"
    elif intent == "summarize":
        return "summarize"
    elif intent in ("qa", "multi_step"):
        return "retrieve_for_qa"
    else:
        return "retrieve_for_qa"  # default fallback


# ── Build the Graph ──────────────────────────────────────────────

def build_graph() -> StateGraph:
    """Construct and compile the Enterprise Ops Copilot graph."""

    graph = StateGraph(AgentState)

    # Add all nodes
    graph.add_node("ingest_user", ingest_user)
    graph.add_node("route_intent", route_intent)
    graph.add_node("budget_guard", budget_guard)
    graph.add_node("retrieve_for_qa", retrieve)
    graph.add_node("retrieve_for_compliance", retrieve)
    graph.add_node("answer_with_citations", answer_with_citations)
    graph.add_node("execute_action", execute_action)
    graph.add_node("compliance_check", compliance_check)
    graph.add_node("summarize", summarize)
    graph.add_node("final_response", final_response)

    # Entry point
    graph.add_edge(START, "ingest_user")
    graph.add_edge("ingest_user", "route_intent")
    graph.add_edge("route_intent", "budget_guard")

    # Budget guard: blocked → final, continue → skill branch
    graph.add_conditional_edges(
        "budget_guard",
        should_stop_for_budget,
        {
            "blocked": "final_response",
            "continue": "skill_router",
        },
    )

    # Invisible routing node — fans out by intent
    graph.add_node("skill_router", lambda state: state)  # pass-through
    graph.add_conditional_edges(
        "skill_router",
        route_by_intent,
        {
            "retrieve_for_qa": "retrieve_for_qa",
            "retrieve_for_compliance": "retrieve_for_compliance",
            "execute_action": "execute_action",
            "summarize": "summarize",
        },
    )

    # QA path: retrieve → answer → final
    graph.add_edge("retrieve_for_qa", "answer_with_citations")
    graph.add_edge("answer_with_citations", "final_response")

    # Compliance path: retrieve → compliance_check → final
    graph.add_edge("retrieve_for_compliance", "compliance_check")
    graph.add_edge("compliance_check", "final_response")

    # Action path: execute → final
    graph.add_edge("execute_action", "final_response")

    # Summarize path: summarize → final
    graph.add_edge("summarize", "final_response")

    # End
    graph.add_edge("final_response", END)

    return graph.compile()


# ── Compiled graph instance ──────────────────────────────────────
copilot_graph = build_graph()
