# __init__.py
"""
Enterprise Ops Copilot — Skills Registry
Exports all skill functions for the graph.
"""
from skills.router import route_intent
from skills.retrieval import retrieve
from skills.answer_with_citations import answer_with_citations
from skills.action_executor import execute_action
from skills.compliance_check import compliance_check
from skills.summarizer import summarize

ALL_SKILLS = {
    "route_intent": route_intent,
    "retrieve": retrieve,
    "answer_with_citations": answer_with_citations,
    "execute_action": execute_action,
    "compliance_check": compliance_check,
    "summarize": summarize,
}