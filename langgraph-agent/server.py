# server.py
"""
Enterprise Ops Copilot — FastAPI Server
HTTP wrapper around the LangGraph agent.
NestJS backend calls these endpoints.
"""
from __future__ import annotations
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from langchain_core.messages import HumanMessage
from graph import copilot_graph

app = FastAPI(
    title="Enterprise Ops Copilot — LangGraph Agent",
    version="1.0.0",
    description="ReAct reasoning engine for the Enterprise Ops Copilot",
)


# ── Request/Response Models ──────────────────────────────────────

class QueryRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    user_role: str = "support_agent"


class ActionRequest(BaseModel):
    action: str
    payload: dict
    session_id: Optional[str] = None


class AgentResponse(BaseModel):
    final_answer: str
    intent: Optional[str] = None
    llm_tier: Optional[int] = None
    risk_level: Optional[str] = None
    total_cost: float = 0.0
    citations: list[str] = []
    trace_log: list[dict] = []


# ── Endpoints ────────────────────────────────────────────────────

@app.post("/agent/query", response_model=AgentResponse)
async def query_agent(req: QueryRequest):
    """Send a question to the ReAct agent."""
    try:
        initial_state = {
            "messages": [HumanMessage(content=req.question)],
        }

        result = copilot_graph.invoke(initial_state)

        return AgentResponse(
            final_answer=result.get("final_answer", "No answer generated."),
            intent=result.get("intent"),
            llm_tier=result.get("llm_tier"),
            risk_level=result.get("risk_level"),
            total_cost=result.get("total_cost", 0.0),
            citations=result.get("citations", []),
            trace_log=result.get("trace_log", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/action", response_model=AgentResponse)
async def execute_action(req: ActionRequest):
    """Execute an action through the agent."""
    try:
        # Frame the action as a message
        message = f"[ACTION: {req.action}] {str(req.payload)}"
        initial_state = {
            "messages": [HumanMessage(content=message)],
        }

        result = copilot_graph.invoke(initial_state)

        return AgentResponse(
            final_answer=result.get("final_answer", "Action could not be completed."),
            intent=result.get("intent"),
            llm_tier=result.get("llm_tier"),
            total_cost=result.get("total_cost", 0.0),
            trace_log=result.get("trace_log", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok", "service": "langgraph-agent", "mock_mode": True}