"""Tool: Safe calculator."""
from langchain_core.tools import tool


@tool
def calculator(expression: str) -> dict:
    """Evaluate a math expression. Only supports numbers and basic operators (+, -, *, /, ())."""
    sanitized = expression.replace(" ", "")

    # Safety: only allow numbers and basic math operators
    allowed = set("0123456789+-*/.()%")
    if not all(c in allowed for c in sanitized):
        return {"error": f"Invalid characters in expression: {expression}"}

    try:
        result = eval(sanitized, {"__builtins__": {}}, {})
        return {"expression": expression, "result": result}
    except Exception as e:
        return {"error": f"Failed to evaluate: {str(e)}"}