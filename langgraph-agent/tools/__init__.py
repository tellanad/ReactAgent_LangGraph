# __init__.py
"""
Enterprise Ops Copilot — Tool Registry
Exports all tools as a list for LangGraph binding.
"""
from tools.search_docs import search_docs
from tools.salesforce_lookup import salesforce_lookup
from tools.cpq_rules import cpq_rules_lookup
from tools.jira_ticket import create_jira_ticket
from tools.calculator import calculator

ALL_TOOLS = [
    search_docs,
    salesforce_lookup,
    cpq_rules_lookup,
    create_jira_ticket,
    calculator,
]

TOOL_MAP = {tool.name: tool for tool in ALL_TOOLS}