"""
=============================================================================
backend/agent/graph.py — LANGGRAPH GRAPH + RUNNER
=============================================================================
"""

import time
from langgraph.graph import END, START, StateGraph
from backend.core.websocket import ws_manager  # ✅ Fixed: circular import hataya
from backend.agent.nodes.finalize_node import error_handler_node, finalize_node
from backend.agent.nodes.jira_creator_node import create_jira_issue_node
from backend.agent.nodes.pr_action_node import act_on_pr_node
from backend.agent.nodes.pr_analyzer_node import analyze_pr_node
from backend.agent.nodes.router_node import router_node
from backend.agent.nodes.slack_notifier_node import notify_slack_node
from backend.agent.state import AgentState
from backend.core.logger import get_logger
from backend.models.events import IncomingEvent
from backend.models.responses import OrchestratorResponse
from backend.agent.nodes.summarize_node import summarize_push_node

logger = get_logger(__name__)


def _build_graph():
    """LangGraph graph banao aur compile karo."""
    graph = StateGraph(AgentState)

    # Nodes register karo
    graph.add_node("summarize",          summarize_push_node)
    graph.add_node("router",             router_node)
    graph.add_node("analyze_pr",         analyze_pr_node)
    graph.add_node("act_on_pr",          act_on_pr_node)
    graph.add_node("create_jira_issue",  create_jira_issue_node)
    graph.add_node("notify_slack",       notify_slack_node)
    graph.add_node("finalize",           finalize_node)
    graph.add_node("handle_error",       error_handler_node)

    # Entry point
    graph.set_entry_point("summarize")
    graph.add_edge("summarize", "router")

    # Conditional routing
    graph.add_conditional_edges(
        "router",
        lambda state: state["next_action"],
        {
            "analyze_pr":        "analyze_pr",
            "create_jira_issue": "create_jira_issue",
            "notify_slack":      "notify_slack",
            "handle_error":      "handle_error",
        },
    )

    # Fixed edges
    graph.add_edge("analyze_pr",        "act_on_pr")
    graph.add_edge("act_on_pr",         "notify_slack")   # ✅ PR action ke baad Slack notify
    graph.add_edge("create_jira_issue", "notify_slack")   # ✅ Jira ke baad Slack notify
    graph.add_edge("notify_slack",      "finalize")
    graph.add_edge("finalize",          END)
    graph.add_edge("handle_error",      END)

    compiled = graph.compile()
    logger.info("LangGraph compiled successfully")
    return compiled


_AGENT_GRAPH = _build_graph()


async def run_agent(event: IncomingEvent) -> OrchestratorResponse:
    """AI agent run karo with live Frontend Broadcasting."""
    start_time = time.time()

    await ws_manager.broadcast({
        "type": "agent_log",
        "message": f"🚀 <b>LangGraph Orchestrator</b> started for event: {event.event_type.value}"
    })

    await ws_manager.broadcast({
        "type": "agent_log",
        "message": "🔍 <b>Step 1:</b> Analyzing PR/Push context..."
    })

    initial_state: AgentState = {
        "event":            event,
        "messages":         [],
        "pr_analysis":      None,
        "analysis_summary": None,
        "next_action":      "",
        "actions_taken":    [],
        "errors":           [],
        "final_response":   None,
    }

    final_state = await _AGENT_GRAPH.ainvoke(initial_state)

    for action in final_state.get("actions_taken", []):
        await ws_manager.broadcast({
            "type": "agent_log",
            "message": f"⚙️ <b>Action Performed:</b> {action}"
        })

    elapsed_ms = (time.time() - start_time) * 1000

    response = final_state.get("final_response") or OrchestratorResponse(
        success=False,
        event_type=event.event_type,
        errors=["No final_response in state"],
    )
    response.processing_time_ms = elapsed_ms

    if response and response.success:
        await ws_manager.broadcast({
            "type": "agent_log",
            "message": f"✅ <b>Agent Pipeline</b> completed in {elapsed_ms:.0f}ms."
        })
    else:
        await ws_manager.broadcast({
            "type": "agent_log",
            "message": "❌ <b>Agent Pipeline</b> failed with errors."
        })

    logger.info(f"[Agent] Done | success={response.success} | actions={response.actions_taken}")
    return response