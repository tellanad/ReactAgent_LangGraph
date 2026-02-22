"""
Skill 4: Action Executor
Handles tasks like "create ticket", "draft email", "generate checklist".
Uses Tier 0 LLM to parse intent, then calls the right tool.
"""
from __future__ import annotations
import json
from langchain_core.messages import HumanMessage, SystemMessage
from state import AgentState
from llm_selector import get_llm, estimate_cost
from prompts.registry import prompt_registry
from tools import TOOL_MAP


def execute_action(state: AgentState) -> dict:
    """Parse the user request and execute the appropriate tool.
    
    Reads: messages, required_tools
    Sets: final_answer, action_result
    Appends to: trace_log, total_cost
    """
    messages = state.get("messages", [])
    required_tools = state.get("required_tools", [])

    if not messages:
        return {"final_answer": "No request to execute.", "error": "No messages"}

    question = messages[-1].content if hasattr(messages[-1], "content") else str(messages[-1])

    # Use Tier 0 to parse the action into tool call params
    system_prompt = prompt_registry.render(
        "action", "v1",
        action_type=state.get("intent", "action"),
        available_tools=", ".join(required_tools),
    )

    llm = get_llm(tier=0)
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=question),
    ])

    # Parse LLM response to get tool name + params
    try:
        plan = json.loads(response.content)
        # If LLM returned router-style JSON instead of action plan, use fallback
        if "tool" not in plan:
            plan = _fallback_parse(question, required_tools)
    except json.JSONDecodeError:
        plan = _fallback_parse(question, required_tools)

    tool_name = plan.get("tool", "")
    params = plan.get("params", {})
    user_message = plan.get("user_message", "")

    # Execute the tool
    action_result = {}
    if tool_name in TOOL_MAP:
        try:
            tool_fn = TOOL_MAP[tool_name]
            action_result = tool_fn.invoke(params)
        except Exception as e:
            action_result = {"error": f"Tool '{tool_name}' failed: {str(e)}"}
    else:
        action_result = {"error": f"Tool '{tool_name}' not found"}

    # Build final answer
    if "error" in action_result:
        final_answer = f"Action failed: {action_result['error']}"
    else:
        final_answer = _format_action_result(tool_name, action_result, user_message)

    # Cost tracking
    usage = getattr(response, "usage_metadata", {})
    input_tokens = usage.get("input_tokens", 50)
    output_tokens = usage.get("output_tokens", 30)
    step_cost = estimate_cost(0, input_tokens, output_tokens)

    trace_entry = {
        "node": "execute_action",
        "model": "tier_0",
        "tool_called": tool_name,
        "tool_params": params,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost": step_cost,
    }

    prev_cost = state.get("total_cost", 0.0)
    prev_trace = state.get("trace_log", [])

    return {
        "final_answer": final_answer,
        "action_result": action_result,
        "total_cost": prev_cost + step_cost,
        "trace_log": prev_trace + [trace_entry],
        "current_node": "execute_action",
    }


def _fallback_parse(question: str, tools: list[str]) -> dict:
    """Fallback when LLM doesn't return valid JSON."""
    q_lower = question.lower()

    if "ticket" in q_lower or "jira" in q_lower:
        return {
            "tool": "create_jira_ticket",
            "params": {"summary": question[:100], "description": question, "priority": "Medium"},
            "user_message": "Creating a Jira ticket for you.",
        }
    if "calculate" in q_lower or any(op in q_lower for op in ["+", "-", "*", "/"]):
        # Strip non-math text, keep only the expression
        import re
        expr = re.sub(r'[^0-9+\-*/.() ]', '', question).strip()
        return {
            "tool": "calculator",
            "params": {"expression": expr},
            "user_message": "Calculating...",
        }
    if "cpq" in q_lower or "quote" in q_lower or "pricing" in q_lower:
        return {
            "tool": "cpq_rules_lookup",
            "params": {"product": "enterprise suite"},
            "user_message": "Looking up CPQ rules.",
        }

    return {"tool": tools[0] if tools else "", "params": {}, "user_message": "Attempting action."}


def _format_action_result(tool_name: str, result: dict, user_message: str) -> str:
    """Format tool result into a readable response."""
    if tool_name == "create_jira_ticket":
        tid = result.get("ticket_id", "???")
        url = result.get("url", "")
        return f"Done! Created Jira ticket **{tid}**.\nURL: {url}\nStatus: {result.get('status', 'Open')}"

    if tool_name == "calculator":
        return f"Result: {result.get('expression', '?')} = **{result.get('result', '?')}**"

    if tool_name == "cpq_rules_lookup":
        product = result.get("product", "?")
        checklist = result.get("checklist", [])
        items = "\n".join(f"  - {item}" for item in checklist)
        return f"CPQ Checklist for {product}:\n{items}"

    # Generic fallback
    if user_message:
        return f"{user_message}\n\nResult: {json.dumps(result, indent=2)}"
    return json.dumps(result, indent=2)