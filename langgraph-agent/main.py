"""
Enterprise Ops Copilot — CLI Interface
Interactive chat loop for testing the agent locally.
Shows routing decisions, model tier, cost per turn, and total cost.
"""
from __future__ import annotations
from langchain_core.messages import HumanMessage
from colorama import init, Fore, Style
from graph import copilot_graph
from config import MAX_BUDGET_PER_RUN

init(autoreset=True)


def print_banner():
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"  Enterprise Ops Copilot — ReAct Agent (Mock Mode)")
    print(f"  Budget: ${MAX_BUDGET_PER_RUN:.2f} per run")
    print(f"{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Try these example queries:")
    print(f"  • What is the refund policy? Cite sources.")
    print(f"  • Summarize case CASE-001")
    print(f"  • Create a Jira ticket for login bug on mobile")
    print(f"  • Is this medical claim compliant?")
    print(f"  • CPQ checklist for Enterprise Suite")
    print(f"  • Calculate 25000 * 0.85")
    print(f"{Fore.CYAN}Type 'quit' or 'exit' to stop.{Style.RESET_ALL}\n")


def print_trace(trace_log: list[dict]):
    """Print execution trace with formatting."""
    if not trace_log:
        return
    print(f"\n{Fore.WHITE}{Style.DIM}── Execution Trace ──")
    for entry in trace_log:
        node = entry.get("node", "?")
        model = entry.get("model", "—")
        cost = entry.get("cost", 0.0)
        action = entry.get("action", "")
        extra = ""
        if action:
            extra = f" [{action}]"
        if entry.get("chunks_found") is not None:
            extra = f" [chunks: {entry['chunks_found']}]"
        if entry.get("tool_called"):
            extra = f" [tool: {entry['tool_called']}]"
        print(f"  {node:<30} model={model:<8} cost=${cost:.6f}{extra}")
    print(f"{'─'*50}{Style.RESET_ALL}")


def main():
    print_banner()
    session_cost = 0.0

    while True:
        try:
            user_input = input(f"{Fore.GREEN}You > {Style.RESET_ALL}").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{Fore.CYAN}Goodbye!{Style.RESET_ALL}")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print(f"{Fore.CYAN}Goodbye! Session cost: ${session_cost:.6f}{Style.RESET_ALL}")
            break

        # Run the agent
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
        }

        try:
            result = copilot_graph.invoke(initial_state)
        except Exception as e:
            print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
            continue

        # Extract results
        answer = result.get("final_answer", "No answer.")
        intent = result.get("intent", "?")
        tier = result.get("llm_tier", "?")
        risk = result.get("risk_level", "?")
        cost = result.get("total_cost", 0.0)
        trace = result.get("trace_log", [])

        session_cost += cost

        # Display routing info
        risk_color = Fore.RED if risk in ("high", "critical") else Fore.YELLOW if risk == "medium" else Fore.GREEN
        print(f"\n{Fore.MAGENTA}[intent={intent}  tier={tier}  risk={risk_color}{risk}{Fore.MAGENTA}  cost=${cost:.6f}  session=${session_cost:.6f}]{Style.RESET_ALL}")

        # Display answer
        print(f"\n{Fore.CYAN}Agent > {Style.RESET_ALL}{answer}")

        # Display trace
        print_trace(trace)
        print()


if __name__ == "__main__":
    main()